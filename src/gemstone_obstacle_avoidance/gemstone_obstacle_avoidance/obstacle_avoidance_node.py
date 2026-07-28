"""gemstone_obstacle_avoidance: /scan verisine bakip ileri hareketi guvenli
hale getiren karar node'u.

Bu node bir "guvenlik katmani" gibi calisir: teleop veya Nav2'den gelen hiz
komutunu (input_cmd_vel_topic) dinler, on konide engel varsa ileri hizi
sifirlar, sonucu motor_driver'in dinledigi topic'e (output_cmd_vel_topic)
yeniden yayinlar. Boylece Nav2 kurulmadan da tek basina calisip temel
engelden kacinma/acil dur saglayabilir.

Guvenlik prensibi (fail-safe): lidar verisi scan_timeout suresinden uzun
sure gelmezse "engel yok" degil "engel var" varsayilir, yani ileri hareket
lidar veri saglamiyorsa durdurulur.
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

from gemstone_obstacle_avoidance.lidar_safety import (
    compute_min_forward_distance,
    limit_twist,
)


class ObstacleAvoidanceNode(Node):

    def __init__(self):
        super().__init__('obstacle_avoidance_node')

        self.declare_parameter('scan_topic', 'scan')
        self.declare_parameter('input_cmd_vel_topic', 'cmd_vel_nav')
        self.declare_parameter('output_cmd_vel_topic', 'cmd_vel')
        self.declare_parameter('safety_distance', 0.4)
        self.declare_parameter('forward_half_angle_deg', 30.0)
        self.declare_parameter('forward_angle_offset_deg', 0.0)
        self.declare_parameter('scan_timeout', 0.5)

        self.safety_distance = self.get_parameter('safety_distance').value
        self.forward_half_angle_rad = math.radians(
            self.get_parameter('forward_half_angle_deg').value)
        self.forward_angle_offset_rad = math.radians(
            self.get_parameter('forward_angle_offset_deg').value)
        self.scan_timeout = self.get_parameter('scan_timeout').value

        self.latest_min_distance = math.inf
        self.latest_scan_time = None

        scan_topic = self.get_parameter('scan_topic').value
        input_topic = self.get_parameter('input_cmd_vel_topic').value
        output_topic = self.get_parameter('output_cmd_vel_topic').value

        self.create_subscription(LaserScan, scan_topic, self.scan_cb, 10)
        self.create_subscription(Twist, input_topic, self.cmd_vel_cb, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, output_topic, 10)
        self.blocked_pub = self.create_publisher(Bool, 'obstacle_avoidance/blocked', 10)

        self.get_logger().info(
            f'Engelden kacinma basladi: {scan_topic} + {input_topic} -> {output_topic}, '
            f'safety_distance={self.safety_distance} m, '
            f'forward_half_angle={self.get_parameter("forward_half_angle_deg").value} deg')

    def scan_cb(self, msg: LaserScan):
        self.latest_min_distance = compute_min_forward_distance(
            ranges=msg.ranges,
            angle_min=msg.angle_min,
            angle_increment=msg.angle_increment,
            range_min=msg.range_min,
            range_max=msg.range_max,
            forward_half_angle_rad=self.forward_half_angle_rad,
            forward_angle_offset_rad=self.forward_angle_offset_rad,
        )
        self.latest_scan_time = self.get_clock().now()

    def cmd_vel_cb(self, msg: Twist):
        stale = (
            self.latest_scan_time is None
            or (self.get_clock().now() - self.latest_scan_time).nanoseconds / 1e9 > self.scan_timeout
        )
        # Fail-safe: lidar verisi bayatsa engel varmis gibi davran (0.0 mesafe).
        effective_min_distance = 0.0 if stale else self.latest_min_distance

        result = limit_twist(
            msg.linear.x, msg.angular.z, effective_min_distance, self.safety_distance)

        out = Twist()
        out.linear.x = result.linear_x
        out.angular.z = result.angular_z
        self.cmd_vel_pub.publish(out)
        self.blocked_pub.publish(Bool(data=result.blocked))

        if stale:
            self.get_logger().warn(
                'Lidar verisi bayat, ileri hareket guvenlik icin engellendi.',
                throttle_duration_sec=2.0)
        elif result.blocked:
            self.get_logger().warn(
                f'On tarafta engel ({self.latest_min_distance:.2f} m), ileri hiz sifirlandi.',
                throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
