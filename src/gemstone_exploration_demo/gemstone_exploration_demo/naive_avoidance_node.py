"""naive_avoidance_node: enansakib/obstacle-avoidance-turtlebot'taki basit
esik tabanli engelden kacinma algoritmasinin ROS 2 dugumu.

/scan'e bakip on ve on-sol/on-sag mesafelerini cikarir, yol acikken ileri
gider, degilse sabit yonde doner. `cmd_vel_nav`'a yayinlar (dogrudan
`cmd_vel`'e degil) ki `gemstone_obstacle_avoidance/obstacle_avoidance_node`
guvenlik filtresinden gecsin -- projedeki diger otonom hareket kaynagi
(`gemstone_exploration_demo`) ile ayni guvenlik katmanini paylasir.

Varsayilan olarak KAPALI (bkz. bringup launch `enable_naive_avoidance`):
projenin asil otonom hareket davranisi `gemstone_exploration_demo`'daki
durum makineli algoritma, bu node onun daha basit/ogretici alternatifi.
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from gemstone_exploration_demo.naive_obstacle_avoidance import decide_naive_avoidance
from gemstone_obstacle_avoidance.lidar_safety import compute_min_forward_distance


class NaiveAvoidanceNode(Node):

    def __init__(self):
        super().__init__('naive_avoidance_node')

        self.declare_parameter('scan_topic', 'scan')
        self.declare_parameter('output_cmd_vel_topic', 'cmd_vel_nav')
        self.declare_parameter('distance_threshold', 0.8)
        self.declare_parameter('side_angle_deg', 15.0)
        self.declare_parameter('beam_half_angle_deg', 3.0)
        self.declare_parameter('forward_speed', 0.15)
        self.declare_parameter('turn_speed', 0.4)

        self.scan_topic = self.get_parameter('scan_topic').value
        self.output_topic = self.get_parameter('output_cmd_vel_topic').value
        self.distance_threshold = self.get_parameter('distance_threshold').value
        self.side_angle_rad = math.radians(self.get_parameter('side_angle_deg').value)
        self.beam_half_angle_rad = math.radians(
            self.get_parameter('beam_half_angle_deg').value)
        self.forward_speed = self.get_parameter('forward_speed').value
        self.turn_speed = self.get_parameter('turn_speed').value

        self.cmd_pub = self.create_publisher(Twist, self.output_topic, 10)
        self.create_subscription(LaserScan, self.scan_topic, self.scan_cb, 10)

        self.get_logger().info(
            f'Naive avoidance basladi: {self.scan_topic} -> {self.output_topic}, '
            f'threshold={self.distance_threshold} m, '
            f'side_angle={self.get_parameter("side_angle_deg").value} deg')

    def scan_cb(self, msg: LaserScan):
        common = dict(
            ranges=msg.ranges,
            angle_min=msg.angle_min,
            angle_increment=msg.angle_increment,
            range_min=msg.range_min,
            range_max=msg.range_max,
            forward_half_angle_rad=self.beam_half_angle_rad,
        )
        front = compute_min_forward_distance(forward_angle_offset_rad=0.0, **common)
        left = compute_min_forward_distance(
            forward_angle_offset_rad=self.side_angle_rad, **common)
        right = compute_min_forward_distance(
            forward_angle_offset_rad=-self.side_angle_rad, **common)

        command = decide_naive_avoidance(
            front_distance=front,
            left_distance=left,
            right_distance=right,
            distance_threshold=self.distance_threshold,
            forward_speed=self.forward_speed,
            turn_speed=self.turn_speed,
        )

        twist = Twist()
        twist.linear.x = command.linear_x
        twist.angular.z = command.angular_z
        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = NaiveAvoidanceNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
