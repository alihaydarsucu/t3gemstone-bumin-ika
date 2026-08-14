"""frontier_explorer_node: otonom oda kesif duzenleyicisi.

Akim:
  /map (transient_local) + tf(map->base_link)
      -> FrontierDetector.detect  (wavefront BFS, kumeleme)
      -> FrontierManager.update   (kalici kayitlar, dwell-visit)
      -> goal_selection           (utility + commit margin)
      -> nav2_msgs/action/NavigateToPose goal gonderimi

Yayinlar:
  /exploration/frontiers   MarkerArray (frontier kumeleri)
  /exploration/current_goal Marker (ok hedefi)
  /exploration/status      std_msgs/String (RUNNING/DONE/IDLE/...)
  /exploration/coverage    std_msgs/Float32 (bilinen harita orani)

Servisler:
  /exploration/start  std_srvs/Trigger — kesifi baslat
  /exploration/stop   std_srvs/Trigger — kesifi durdur (hedef iptal)
  /exploration/save_map std_srvs/Trigger — slam_toolbox harita kaydi

Kullanilan hedef akisi guvenlik katmaniyla uyumludur:
  Nav2 ciktilari cmd_vel_nav -> obstacle_avoidance_node -> cmd_vel -> motor.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy

from geometry_msgs.msg import Quaternion
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import Float32, String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
from visualization_msgs.msg import Marker, MarkerArray

from .coverage import compute_coverage
from .frontier_detection import (FrontierCluster, FrontierDetector,
                                 FrontierDetectorParams)
from .frontier_manager import (FrontierManager, FrontierManagerParams,
                               FrontierRecord)
from .goal_selection import (select_goal_with_commit, goal_pose_for_point)
from .occupancy_grid_2d import GridExtent, OccupancyGrid2D

# slam_toolbox SaveMap sonuc kodlari
SAVE_MAP_RESULT_SUCCESS = 0


def _yaw_to_quat(yaw: float) -> Quaternion:
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class FrontierExplorerNode(Node):
    """Kesif akisini yuruten ROS 2 duzenleyici node."""

    def __init__(self):
        super().__init__('frontier_explorer_node')
        # use_sim_time: launch'in --params-file'i uzerinden rclpy tarafindan
        # otomatik bildirilir (automatically_declare_parameters_from_overrides).
        # Burada tekrar declare etmek ParameterAlreadyDeclaredException'a yol
        # acar; saat zaten get_clock() uzerinden use_sim_time'i okur.
        self.declare_parameter('map_topic', '/map')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('map_save_service', '/slam_toolbox/save_map')
        self.declare_parameter('action_name', '/navigate_to_pose')
        self.declare_parameter('detect_period', 1.0)
        self.declare_parameter('publish_period', 1.0)

        self.declare_parameter('cluster_min_cells', 8)
        self.declare_parameter('border_margin_cells', 2)
        self.declare_parameter('obstacle_clearance_cells', 1)
        self.declare_parameter('unknown_bridge_cells', 1)
        self.declare_parameter('robot_snap_radius_m', 1.0)
        self.declare_parameter('bounds_enabled', True)
        self.declare_parameter('bounds_min_x', -6.0)
        self.declare_parameter('bounds_max_x', 6.0)
        self.declare_parameter('bounds_min_y', -4.0)
        self.declare_parameter('bounds_max_y', 4.0)

        self.declare_parameter('merge_radius_m', 1.0)
        self.declare_parameter('centroid_ema_alpha', 0.5)
        self.declare_parameter('visit_radius_m', 0.6)
        self.declare_parameter('visit_dwell_sec', 1.5)
        self.declare_parameter('max_frontiers', 500)

        self.declare_parameter('w_size', 1.0)
        self.declare_parameter('w_dist', 2.0)
        self.declare_parameter('size_ref_m2', 5.0)
        self.declare_parameter('dist_ref_m', 25.0)
        self.declare_parameter('goal_select_threshold', -1.0e9)
        self.declare_parameter('commit_margin', 0.05)
        self.declare_parameter('pursuit_timeout_min_sec', 10.0)
        self.declare_parameter('goal_snap_radius_m', 0.5)

        self.declare_parameter('coverage_threshold', 0.99)

        # ---- durum ----
        self._active = False
        self._exploration_done = False
        self._latest_grid: OccupancyGrid2D | None = None
        self._latest_map_msg: OccupancyGrid | None = None
        self._current_record_id: int | None = None
        self._goal_in_flight = False

        # ---- mantik nesneleri ----
        self._detector = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=self.get_parameter('cluster_min_cells').value,
            border_margin_cells=self.get_parameter('border_margin_cells').value,
            obstacle_clearance_cells=self.get_parameter('obstacle_clearance_cells').value,
            unknown_bridge_cells=self.get_parameter('unknown_bridge_cells').value,
            robot_snap_radius_m=self.get_parameter('robot_snap_radius_m').value,
            bounds_enabled=self.get_parameter('bounds_enabled').value,
            bounds_min_x=self.get_parameter('bounds_min_x').value,
            bounds_max_x=self.get_parameter('bounds_max_x').value,
            bounds_min_y=self.get_parameter('bounds_min_y').value,
            bounds_max_y=self.get_parameter('bounds_max_y').value,
        ))
        self._extent = self._detector.params.to_extent()

        self._manager = FrontierManager(FrontierManagerParams(
            merge_radius_m=self.get_parameter('merge_radius_m').value,
            centroid_ema_alpha=self.get_parameter('centroid_ema_alpha').value,
            visit_radius_m=self.get_parameter('visit_radius_m').value,
            visit_dwell_sec=self.get_parameter('visit_dwell_sec').value,
            max_frontiers=self.get_parameter('max_frontiers').value,
            w_size=self.get_parameter('w_size').value,
            w_dist=self.get_parameter('w_dist').value,
            size_ref_m2=self.get_parameter('size_ref_m2').value,
            dist_ref_m=self.get_parameter('dist_ref_m').value,
            goal_select_threshold=self.get_parameter('goal_select_threshold').value,
            pursuit_timeout_min_sec=self.get_parameter('pursuit_timeout_min_sec').value,
        ))
        self._commit_margin = self.get_parameter('commit_margin').value
        self._goal_snap_radius_m = self.get_parameter('goal_snap_radius_m').value
        self._coverage_threshold = self.get_parameter('coverage_threshold').value

        # ---- ROS altyapisi ----
        map_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            depth=1)
        self._map_sub = self.create_subscription(
            OccupancyGrid, self.get_parameter('map_topic').value,
            self._on_map, map_qos)

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        self._action_client = ActionClient(
            self, NavigateToPose, self.get_parameter('action_name').value)

        # yayincilar
        self._frontier_pub = self.create_publisher(
            MarkerArray, '/exploration/frontiers', 10)
        self._goal_pub = self.create_publisher(
            Marker, '/exploration/current_goal', 10)
        self._status_pub = self.create_publisher(
            String, '/exploration/status', 10)
        self._coverage_pub = self.create_publisher(
            Float32, '/exploration/coverage', 10)

        # servisler
        self._start_srv = self.create_service(
            Trigger, '/exploration/start', self._on_start)
        self._stop_srv = self.create_service(
            Trigger, '/exploration/stop', self._on_stop)
        self._save_map_srv = self.create_service(
            Trigger, '/exploration/save_map', self._on_save_map)

        # zamanlayicilar
        detect_period = self.get_parameter('detect_period').value
        publish_period = self.get_parameter('publish_period').value
        self._detect_timer = self.create_timer(
            detect_period, self._detect_tick)
        self._publish_timer = self.create_timer(
            publish_period, self._publish_tick)

    # ------------------------------------------------------------------
    # Harita / tf / zaman
    # ------------------------------------------------------------------
    def _on_map(self, msg: OccupancyGrid) -> None:
        self._latest_map_msg = msg
        self._latest_grid = OccupancyGrid2D(
            width=msg.info.width, height=msg.info.height,
            resolution=msg.info.resolution,
            origin_x=msg.info.origin.position.x,
            origin_y=msg.info.origin.position.y,
            data=msg.data)

    def _robot_pose(self) -> tuple | None:
        """map -> base_link donusumunden robot (x, y, yaw) degeri."""
        try:
            t = self._tf_buffer.lookup_transform(
                self.get_parameter('map_frame').value,
                self.get_parameter('base_frame').value,
                rclpy.time.Time())
        except (LookupException, ConnectivityException,
                ExtrapolationException):
            return None
        trans = t.transform.translation
        rot = t.transform.rotation
        yaw = math.atan2(
            2.0 * (rot.w * rot.z + rot.x * rot.y),
            1.0 - 2.0 * (rot.y * rot.y + rot.z * rot.z))
        return (trans.x, trans.y, yaw)

    def _now(self) -> float:
        return self.get_clock().now().nanoseconds / 1.0e9

    # ------------------------------------------------------------------
    # Servisler
    # ------------------------------------------------------------------
    def _on_start(self, req, resp: Trigger.Response):
        resp.success = True
        if self._active:
            resp.message = 'Zaten aktif.'
            return resp
        self._active = True
        self._exploration_done = False
        self._current_record_id = None
        self._manager.clear()
        self.get_logger().info('Kesif basladi.')
        resp.message = 'Kesif basladi.'
        return resp

    def _on_stop(self, req, resp: Trigger.Response):
        resp.success = True
        was_active = self._active
        self._active = False
        self._cancel_goal()
        self.get_logger().info('Kesif durduruldu.')
        resp.message = ('Durduruldu.' if was_active
                        else 'Zaten durmus.')
        return resp

    def _on_save_map(self, req, resp: Trigger.Response):
        resp.success = True
        if self._latest_map_msg is None:
            resp.success = False
            resp.message = 'Henuz harita alinmadi.'
            return resp
        try:
            self._save_map_via_slam_toolbox()
        except Exception as exc:  # noqa: BLE001
            resp.success = False
            resp.message = f'Harita kaydedilemedi: {exc}'
            return resp
        resp.message = 'Harita kaydedildi.'
        return resp

    def _save_map_via_slam_toolbox(self) -> None:
        """slam_toolbox /save_map servisiyle harita yazar.

        slam_toolbox, SaveMap.srv'i name bos ise varsayilan yola (calisma
        dizini) kaydeder. map_saver_cli'ye gecilmek istenirse bu fonksiyon
        degistirilebilir.
        """
        from slam_toolbox.srv import SaveMap  # type: ignore[import-untyped]
        from std_msgs.msg import String as StdString
        cli = self.create_client(
            SaveMap, self.get_parameter('map_save_service').value)
        if not cli.wait_for_service(timeout_sec=5.0):
            raise RuntimeError('slam_toolbox save_map servisi yanit vermedi')
        req = SaveMap.Request()
        req.name = StdString(data='')
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self, fut, timeout_sec=10.0)
        if fut.result() is None:
            raise RuntimeError('save_map cagrisi zamandasimi asti')
        if fut.result().result != SAVE_MAP_RESULT_SUCCESS:
            raise RuntimeError(
                f'save_map hata kodu: {fut.result().result}')

    # ------------------------------------------------------------------
    # Deteksiyon cevrimi
    # ------------------------------------------------------------------
    def _detect_tick(self) -> None:
        if not self._active:
            return
        if self._exploration_done:
            return

        grid = self._latest_grid
        if grid is None:
            self._publish_status('WAITING_FOR_MAP')
            return
        pose = self._robot_pose()
        if pose is None:
            self._publish_status('WAITING_FOR_TF')
            return

        t_now = self._now()
        robot_xy = (pose[0], pose[1])

        clusters = self._detector.detect(grid, robot_xy)
        self._manager.update(clusters, robot_xy, t_now)

        coverage = compute_coverage(grid, self._extent)
        self._coverage_pub.publish(Float32(data=float(coverage.ratio)))

        if coverage.ratio >= self._coverage_threshold:
            self._exploration_done = True
            self._cancel_goal()
            self._publish_status(
                f'DONE coverage={coverage.ratio:.3f} '
                f'known_m2={coverage.known_area_m2:.1f}')
            self.get_logger().info(
                f'Kesif tamamlandi: coverage={coverage.ratio:.3f}')
            return

        current = self._manager.find(self._current_record_id) \
            if self._current_record_id is not None else None

        goal_rec = select_goal_with_commit(
            self._manager.active(), robot_xy, self._manager.params,
            current, self._commit_margin)

        if goal_rec is None:
            self._publish_status(
                f'NO_GOAL coverage={coverage.ratio:.3f} '
                f'frontiers={len(clusters)}')
            return

        self._publish_status(
            f'RUNNING coverage={coverage.ratio:.3f} '
            f'frontiers={len(clusters)} goal_id={goal_rec.id} '
            f'goal=({goal_rec.centroid_x:.2f}, {goal_rec.centroid_y:.2f})')

        if self._current_record_id == goal_rec.id and self._goal_in_flight:
            return  # ayni hedefe hala gidiliyor

        self._send_goal(goal_rec, grid)

    def _send_goal(self, rec: FrontierRecord, grid: OccupancyGrid2D) -> None:
        goal_pose = goal_pose_for_point(
            grid, rec.centroid, self._goal_snap_radius_m)
        if goal_pose is None:
            self.get_logger().warning(
                f'Frontier {rec.id} icin BOS hedef bulunamadi; emekliye ayir.')
            self._manager.mark_invalidated(rec.id, self._now())
            self._current_record_id = None
            return

        if not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn(
                'Nav2 NavigateToPose action sunucusu yanit vermiyor.')
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.get_parameter('map_frame').value
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = goal_pose[0]
        goal_msg.pose.pose.position.y = goal_pose[1]
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation = _yaw_to_quat(goal_pose[2])
        goal_msg.behavior_tree = ''

        self._current_record_id = rec.id
        self._manager.mark_selected(rec.id, (goal_pose[0], goal_pose[1]),
                                    self._now())
        self._goal_in_flight = True

        send_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self._on_feedback)
        send_future.add_done_callback(self._on_goal_sent)

    def _on_feedback(self, feedback_msg) -> None:
        pass

    def _on_goal_sent(self, future) -> None:
        goal_handle = future.result()
        if goal_handle is None:
            self.get_logger().error('Nav2 hedef reddetti; goal temizleniyor.')
            self._goal_in_flight = False
            if self._current_record_id is not None:
                self._manager.mark_invalidated(
                    self._current_record_id, self._now())
                self._current_record_id = None
            return
        self._goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_goal_done)

    def _on_goal_done(self, future) -> None:
        self._goal_in_flight = False
        status = future.result().status
        rec_id = self._current_record_id
        if status == 4:  # STATUS_SUCCEEDED
            if rec_id is not None:
                self._manager.mark_visited(rec_id)
        else:
            self.get_logger().warning(
                f'Hedef {rec_id} basarisiz (status={status}).')
            if rec_id is not None:
                self._manager.mark_invalidated(rec_id, self._now())
        self._current_record_id = None

    def _cancel_goal(self) -> None:
        if getattr(self, '_goal_handle', None) is not None:
            cancel_future = self._goal_handle.cancel_goal_async()
            self._goal_handle = None
        self._goal_in_flight = False
        self._current_record_id = None

    # ------------------------------------------------------------------
    # Yayin / durum
    # ------------------------------------------------------------------
    def _publish_status(self, text: str) -> None:
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)

    def _publish_tick(self) -> None:
        # frontier marker'lari ve hedef okunu yayinla
        markers = MarkerArray()
        marker_id = 0

        for rec in self._manager.active():
            m = Marker()
            m.header.frame_id = self.get_parameter('map_frame').value
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = 'frontiers'
            m.id = marker_id
            marker_id += 1
            m.type = Marker.CUBE
            m.action = Marker.ADD
            m.pose.position.x = rec.centroid_x
            m.pose.position.y = rec.centroid_y
            m.pose.position.z = 0.05
            m.pose.orientation.w = 1.0
            size = 0.12
            m.scale.x = size
            m.scale.y = size
            m.scale.z = size
            # boyuta gore renk: buyuk yesil, kucuk sari
            ratio = min(1.0, rec.size_m2 / self._manager.params.size_ref_m2)
            m.color.r = 1.0 - ratio
            m.color.g = ratio
            m.color.b = 0.0
            m.color.a = 0.9
            markers.markers.append(m)

        # hedef oku
        if self._current_record_id is not None:
            rec = self._manager.find(self._current_record_id)
            if rec is not None:
                g = Marker()
                g.header.frame_id = self.get_parameter('map_frame').value
                g.header.stamp = self.get_clock().now().to_msg()
                g.ns = 'current_goal'
                g.id = 0
                g.type = Marker.ARROW
                g.action = Marker.ADD
                g.pose.position.x = rec.centroid_x
                g.pose.position.y = rec.centroid_y
                g.pose.position.z = 0.2
                g.pose.orientation.w = 1.0
                g.scale.x = 0.4
                g.scale.y = 0.08
                g.scale.z = 0.08
                g.color.r = 1.0
                g.color.g = 0.0
                g.color.b = 0.0
                g.color.a = 1.0
                markers.markers.append(g)

        # eski marker'lari temizle
        if markers.markers:
            clear = Marker()
            clear.header.frame_id = self.get_parameter('map_frame').value
            clear.header.stamp = self.get_clock().now().to_msg()
            clear.ns = 'frontiers'
            clear.id = marker_id
            clear.action = Marker.DELETEALL
            clear.type = Marker.CUBE
            markers.markers.append(clear)

        self._frontier_pub.publish(markers)


def main(args=None):
    rclpy.init(args=args)
    node = FrontierExplorerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
