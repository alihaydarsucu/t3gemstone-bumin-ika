"""Gemstone icin timestamp kontrollu LiDAR exploration demo node'u."""

from __future__ import annotations

import enum
import math
import random

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

from gemstone_exploration_demo.exploration_demo import (
    ExplorationGoal,
    angular_error,
    bearing_to_goal,
    choose_sector,
    distance_to_goal,
    filter_free_sectors,
    heading_only_goal,
    quaternion_to_yaw,
    scan_to_sectors,
    sector_to_goal,
)


class ExplorationState(enum.Enum):
    SELECT_GOAL = 'select_goal'
    SEEK_GOAL = 'seek_goal'
    WALL_FOLLOW = 'wall_follow'
    RECOVER = 'recover'


class ExplorationDemoNode(Node):

    def __init__(self):
        super().__init__('gemstone_exploration_demo_node')

        self.declare_parameter('scan_topic', 'scan')
        self.declare_parameter('odom_topic', 'motion_state/odom')
        self.declare_parameter('encoder_available_topic', 'motion_state/encoder_available')
        self.declare_parameter('output_cmd_vel_topic', 'cmd_vel_nav')
        self.declare_parameter('scan_timeout', 0.5)
        self.declare_parameter('odom_timeout', 0.5)
        self.declare_parameter('control_rate_hz', 10.0)
        self.declare_parameter('random_seed', 42)
        self.declare_parameter('sector_width_deg', 15.0)
        self.declare_parameter('min_clearance_m', 1.2)
        self.declare_parameter('target_distance_scale', 0.75)
        self.declare_parameter('min_goal_distance_m', 0.8)
        self.declare_parameter('max_goal_distance_m', 2.5)
        self.declare_parameter('goal_tolerance_m', 0.25)
        self.declare_parameter('heading_tolerance_deg', 12.0)
        self.declare_parameter('max_goal_time_sec', 12.0)
        self.declare_parameter('front_obstacle_distance_m', 0.55)
        self.declare_parameter('wall_follow_linear_speed', 0.12)
        self.declare_parameter('wall_follow_angular_gain', 1.6)
        self.declare_parameter('wall_follow_target_side_distance_m', 0.60)
        self.declare_parameter('wall_follow_timeout_sec', 8.0)
        self.declare_parameter('recovery_spin_speed', 0.45)
        self.declare_parameter('recovery_duration_sec', 1.5)
        self.declare_parameter('max_linear_speed', 0.28)
        self.declare_parameter('max_angular_speed', 0.9)
        self.declare_parameter('goal_heading_gain', 1.8)
        self.declare_parameter('goal_distance_gain', 0.6)

        self.scan_topic = self.get_parameter('scan_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.encoder_available_topic = self.get_parameter('encoder_available_topic').value
        self.output_cmd_vel_topic = self.get_parameter('output_cmd_vel_topic').value
        self.scan_timeout = self.get_parameter('scan_timeout').value
        self.odom_timeout = self.get_parameter('odom_timeout').value
        self.control_rate_hz = self.get_parameter('control_rate_hz').value
        self.rng = random.Random(self.get_parameter('random_seed').value)
        self.sector_width_rad = math.radians(self.get_parameter('sector_width_deg').value)
        self.min_clearance_m = self.get_parameter('min_clearance_m').value
        self.target_distance_scale = self.get_parameter('target_distance_scale').value
        self.min_goal_distance_m = self.get_parameter('min_goal_distance_m').value
        self.max_goal_distance_m = self.get_parameter('max_goal_distance_m').value
        self.goal_tolerance_m = self.get_parameter('goal_tolerance_m').value
        self.heading_tolerance_rad = math.radians(
            self.get_parameter('heading_tolerance_deg').value)
        self.max_goal_time_sec = self.get_parameter('max_goal_time_sec').value
        self.front_obstacle_distance_m = self.get_parameter('front_obstacle_distance_m').value
        self.wall_follow_linear_speed = self.get_parameter('wall_follow_linear_speed').value
        self.wall_follow_angular_gain = self.get_parameter('wall_follow_angular_gain').value
        self.wall_follow_target_side_distance_m = self.get_parameter(
            'wall_follow_target_side_distance_m').value
        self.wall_follow_timeout_sec = self.get_parameter('wall_follow_timeout_sec').value
        self.recovery_spin_speed = self.get_parameter('recovery_spin_speed').value
        self.recovery_duration_sec = self.get_parameter('recovery_duration_sec').value
        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
        self.goal_heading_gain = self.get_parameter('goal_heading_gain').value
        self.goal_distance_gain = self.get_parameter('goal_distance_gain').value

        self._latest_scan = None
        self._latest_scan_stamp = None
        self._latest_odom = None
        self._latest_odom_stamp = None
        self._encoder_available = False

        self._state = ExplorationState.SELECT_GOAL
        self._goal: ExplorationGoal | None = None
        self._goal_selected_at = None
        self._wall_follow_started_at = None
        self._recover_started_at = None

        self.create_subscription(LaserScan, self.scan_topic, self.scan_cb, 20)
        self.create_subscription(Odometry, self.odom_topic, self.odom_cb, 20)
        self.create_subscription(Bool, self.encoder_available_topic, self.encoder_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, self.output_cmd_vel_topic, 10)

        self.create_timer(1.0 / self.control_rate_hz, self.control_loop)

        self.get_logger().info(
            'Exploration demo basladi: '
            f'scan={self.scan_topic}, odom={self.odom_topic}, '
            f'cmd={self.output_cmd_vel_topic}')

    def scan_cb(self, msg: LaserScan):
        self._latest_scan = msg
        self._latest_scan_stamp = self._stamp_or_now(msg.header.stamp)

    def odom_cb(self, msg: Odometry):
        self._latest_odom = msg
        self._latest_odom_stamp = self._stamp_or_now(msg.header.stamp)

    def encoder_cb(self, msg: Bool):
        self._encoder_available = bool(msg.data)

    def control_loop(self):
        now = self.get_clock().now()

        if not self._data_is_fresh(now):
            self._publish_stop()
            self._state = ExplorationState.SELECT_GOAL
            self._goal = None
            return

        if self._latest_scan is None or self._latest_odom is None:
            self._publish_stop()
            return

        if self._state == ExplorationState.SELECT_GOAL or self._goal is None:
            if not self._select_goal(now):
                self._start_recover(now)
                return

        if self._state == ExplorationState.RECOVER:
            self._publish_recover(now)
            return

        front_distance, left_distance, right_distance = self._extract_region_distances(
            self._latest_scan)

        if self._goal_expired(now):
            self._publish_stop()
            self._state = ExplorationState.SELECT_GOAL
            self._goal = None
            return

        if self._state == ExplorationState.WALL_FOLLOW:
            self._publish_wall_follow(front_distance, left_distance, right_distance)
            if self._can_resume_seek(now, front_distance):
                self._state = ExplorationState.SEEK_GOAL
            return

        if front_distance < self.front_obstacle_distance_m:
            self._state = ExplorationState.WALL_FOLLOW
            self._wall_follow_started_at = now
            self._publish_wall_follow(front_distance, left_distance, right_distance)
            return

        self._state = ExplorationState.SEEK_GOAL
        self._publish_seek_goal(front_distance, now)

    def _select_goal(self, now):
        scan = self._latest_scan
        odom = self._latest_odom
        if scan is None or odom is None:
            return False

        sectors = scan_to_sectors(
            ranges=scan.ranges,
            angle_min=scan.angle_min,
            angle_increment=scan.angle_increment,
            range_min=scan.range_min,
            range_max=scan.range_max,
            sector_width_rad=self.sector_width_rad,
        )
        free_sectors = filter_free_sectors(sectors, self.min_clearance_m)
        chosen_sector = choose_sector(free_sectors, self.rng)
        if chosen_sector is None:
            self._goal = None
            self._state = ExplorationState.RECOVER
            self._recover_started_at = now
            self.get_logger().warn(
                'Serbest sektor bulunamadi, kurtarma moduna gecildi.',
                throttle_duration_sec=2.0)
            return False

        pose_x = odom.pose.pose.position.x
        pose_y = odom.pose.pose.position.y
        pose_yaw = quaternion_to_yaw(odom.pose.pose.orientation)

        if self._encoder_available:
            self._goal = sector_to_goal(
                pose_x=pose_x,
                pose_y=pose_y,
                pose_yaw=pose_yaw,
                sector=chosen_sector,
                target_distance_scale=self.target_distance_scale,
                min_goal_distance_m=self.min_goal_distance_m,
                max_goal_distance_m=self.max_goal_distance_m,
            )
            self._goal = ExplorationGoal(
                x=self._goal.x,
                y=self._goal.y,
                heading_rad=self._goal.heading_rad,
                distance_m=self._goal.distance_m,
                selected_sector=self._goal.selected_sector,
                mode='odom',
            )
        else:
            self._goal = heading_only_goal(
                pose_yaw=pose_yaw,
                sector=chosen_sector,
                target_distance_scale=self.target_distance_scale,
                min_goal_distance_m=self.min_goal_distance_m,
                max_goal_distance_m=self.max_goal_distance_m,
            )

        self._goal_selected_at = now
        self._wall_follow_started_at = None
        self._state = ExplorationState.SEEK_GOAL

        self.get_logger().info(
            'Yeni hedef secildi: '
            f'mode={self._goal.mode}, '
            f'sector={math.degrees(chosen_sector.center_angle_rad):.1f} deg, '
            f'distance={chosen_sector.min_distance_m:.2f} m')
        return True

    def _goal_expired(self, now):
        if self._goal_selected_at is None:
            return False
        age = (now - self._goal_selected_at).nanoseconds / 1e9
        return age > self.max_goal_time_sec

    def _goal_reached(self, now):
        if self._goal is None or self._latest_odom is None:
            return False

        if self._goal.mode == 'odom' and self._goal.x is not None and self._goal.y is not None:
            pose_x = self._latest_odom.pose.pose.position.x
            pose_y = self._latest_odom.pose.pose.position.y
            return (
                distance_to_goal(pose_x, pose_y, self._goal.x, self._goal.y)
                <= self.goal_tolerance_m
            )

        if self._goal_selected_at is None:
            return False
        elapsed = (now - self._goal_selected_at).nanoseconds / 1e9
        return elapsed >= self._goal.distance_m / max(self.max_linear_speed, 0.05)

    def _publish_seek_goal(self, front_distance: float, now):
        odom = self._latest_odom
        if odom is None or self._goal is None:
            self._publish_stop()
            return

        pose_x = odom.pose.pose.position.x
        pose_y = odom.pose.pose.position.y
        pose_yaw = quaternion_to_yaw(odom.pose.pose.orientation)

        if self._goal.mode == 'odom' and self._goal.x is not None and self._goal.y is not None:
            target_heading = bearing_to_goal(pose_x, pose_y, self._goal.x, self._goal.y)
            distance_error = distance_to_goal(pose_x, pose_y, self._goal.x, self._goal.y)
        else:
            target_heading = self._goal.heading_rad
            distance_error = self._goal.distance_m

        heading_error = angular_error(target_heading, pose_yaw)
        twist = Twist()
        twist.angular.z = max(
            -self.max_angular_speed,
            min(self.max_angular_speed, heading_error * self.goal_heading_gain),
        )

        if abs(heading_error) < self.heading_tolerance_rad and front_distance >= (
            self.front_obstacle_distance_m
        ):
            twist.linear.x = min(
                self.max_linear_speed,
                max(0.0, distance_error * self.goal_distance_gain),
            )
        else:
            twist.linear.x = 0.0

        self.cmd_pub.publish(twist)

        if self._goal_reached(now):
            self._publish_stop()
            self._state = ExplorationState.SELECT_GOAL
            self._goal = None

    def _publish_wall_follow(
        self,
        front_distance: float,
        left_distance: float,
        right_distance: float,
    ):
        twist = Twist()
        follow_left = left_distance >= right_distance
        side_distance = left_distance if follow_left else right_distance
        side_error = self.wall_follow_target_side_distance_m - side_distance
        turn = self.wall_follow_angular_gain * side_error

        if follow_left:
            turn = -turn

        if front_distance < self.front_obstacle_distance_m:
            turn += -0.8 if follow_left else 0.8

        twist.linear.x = 0.0 if front_distance < 0.20 else self.wall_follow_linear_speed
        twist.angular.z = max(
            -self.max_angular_speed,
            min(self.max_angular_speed, turn),
        )
        self.cmd_pub.publish(twist)

    def _publish_recover(self, now):
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = self.recovery_spin_speed
        self.cmd_pub.publish(twist)

        if self._recover_started_at is None:
            self._recover_started_at = now
            return

        elapsed = (now - self._recover_started_at).nanoseconds / 1e9
        if elapsed >= self.recovery_duration_sec:
            self._state = ExplorationState.SELECT_GOAL
            self._recover_started_at = None

    def _can_resume_seek(self, now, front_distance: float):
        if self._goal is None:
            return False
        if front_distance < self.front_obstacle_distance_m:
            return False
        if self._wall_follow_started_at is None:
            return False
        elapsed = (now - self._wall_follow_started_at).nanoseconds / 1e9
        if elapsed > self.wall_follow_timeout_sec:
            self._state = ExplorationState.SELECT_GOAL
            self._goal = None
            return False
        return True

    def _extract_region_distances(self, scan: LaserScan):
        sectors = scan_to_sectors(
            ranges=scan.ranges,
            angle_min=scan.angle_min,
            angle_increment=scan.angle_increment,
            range_min=scan.range_min,
            range_max=scan.range_max,
            sector_width_rad=math.radians(10.0),
        )
        if not sectors:
            return math.inf, math.inf, math.inf

        front = min(
            (
                sector.min_distance_m
                for sector in sectors
                if abs(sector.center_angle_rad) <= math.radians(20.0)
            ),
            default=math.inf,
        )
        left = min(
            (
                sector.min_distance_m
                for sector in sectors
                if math.radians(20.0) < sector.center_angle_rad <= math.radians(100.0)
            ),
            default=math.inf,
        )
        right = min(
            (
                sector.min_distance_m
                for sector in sectors
                if -math.radians(100.0) <= sector.center_angle_rad < -math.radians(20.0)
            ),
            default=math.inf,
        )
        return front, left, right

    def _data_is_fresh(self, now):
        if self._latest_scan_stamp is None or self._latest_odom_stamp is None:
            return False
        scan_age = (now - self._latest_scan_stamp).nanoseconds / 1e9
        odom_age = (now - self._latest_odom_stamp).nanoseconds / 1e9
        if scan_age > self.scan_timeout or odom_age > self.odom_timeout:
            self.get_logger().warn(
                f'Data bayat: scan_age={scan_age:.2f}s, odom_age={odom_age:.2f}s',
                throttle_duration_sec=2.0)
            return False
        return True

    def _start_recover(self, now):
        self._state = ExplorationState.RECOVER
        self._recover_started_at = now
        self._publish_stop()

    def _publish_stop(self):
        self.cmd_pub.publish(Twist())

    def _stamp_or_now(self, stamp_msg):
        if stamp_msg.sec == 0 and stamp_msg.nanosec == 0:
            return self.get_clock().now()
        return Time.from_msg(stamp_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ExplorationDemoNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
