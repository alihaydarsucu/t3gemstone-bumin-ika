"""gemstone_motor_driver: /cmd_vel (geometry_msgs/Twist) komutunu
diferansiyel surus kinematigiyle sol/sag teker yonune cevirip Gemstone'un
GPIO'lari uzerinden (libgpiod) Harezmi kartindaki MX1508 H-bridge'i suren,
ve kadratur enkoderlerden tekerlek odometrisi (nav_msgs/Odometry) ureten
node.

Mimari notu: Bu node artik harici bir surucu karta UART ile KOMUT
GONDERMIYOR -- Gemstone, Harezmi kartindaki Deneyap'in yerini alarak
motorlari VE enkoderleri DOGRUDAN GPIO uzerinden suruyor/okuyor (bkz.
BLUEPRINT.md, mimari karar guncellemesi).

Guvenlik: /cmd_vel belirli bir sure (cmd_vel_timeout) icinde gelmezse
motorlar otomatik durur (watchdog), tipki eski UART implementasyonunda
oldugu gibi.

TF notu: Bu node varsayilan olarak SADECE /wheel_odom topic'ini yayinlar,
odom->base_link TF'ini YAYINLAMAZ (publish_tf parametresi False) --
cunku bu TF'i su an rf2o_laser_odometry sagliyor (publish_tf:true). Ikisi
birden TF yayinlarsa cakisir (TF_REPEATED_DATA). Ileride robot_localization
(EKF) ile bu iki odometri kaynagini (teker + lazer) birlestirmek en dogru
yontem olacak.
"""

import gpiod

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from tf_transformations import quaternion_from_euler

from gemstone_motor_driver.differential_drive import (
    twist_to_wheel_speeds,
    wheel_speed_to_percent,
    wheel_speeds_to_twist,
    ticks_to_distance,
    OdometryIntegrator,
)
from gemstone_motor_driver.gpio_motor import GpioHBridgeMotor
from gemstone_motor_driver.quadrature_encoder import QuadratureEncoder


class MotorDriverNode(Node):

    def __init__(self):
        super().__init__('motor_driver_node')

        self.declare_parameter('gpio_chip', '')
        self.declare_parameter('motor1_in1_line', -1)
        self.declare_parameter('motor1_in2_line', -1)
        self.declare_parameter('motor2_in1_line', -1)
        self.declare_parameter('motor2_in2_line', -1)
        self.declare_parameter('motor1_invert', False)
        self.declare_parameter('motor2_invert', False)

        self.declare_parameter('encoder1_a_line', -1)
        self.declare_parameter('encoder1_b_line', -1)
        self.declare_parameter('encoder2_a_line', -1)
        self.declare_parameter('encoder2_b_line', -1)
        self.declare_parameter('encoder1_invert', False)
        self.declare_parameter('encoder2_invert', False)
        # YER TUTUCU: motorun/enkoderin gercek cozunurlugu bilinmiyor.
        # Tekerlegi elle tam bir tur cevirip tik sayisini sayarak bulun.
        self.declare_parameter('encoder_ticks_per_revolution', 20.0)
        self.declare_parameter('wheel_radius', 0.033)

        self.declare_parameter('wheel_separation', 0.30)
        self.declare_parameter('max_wheel_speed', 1.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)
        self.declare_parameter('control_rate_hz', 20.0)
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('base_frame_id', 'base_link')
        self.declare_parameter('publish_tf', False)

        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.max_wheel_speed = self.get_parameter('max_wheel_speed').value
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').value
        self.ticks_per_rev = self.get_parameter('encoder_ticks_per_revolution').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.odom_frame_id = self.get_parameter('odom_frame_id').value
        self.base_frame_id = self.get_parameter('base_frame_id').value
        self.publish_tf = self.get_parameter('publish_tf').value

        gpio_chip_name = self.get_parameter('gpio_chip').value
        if not gpio_chip_name:
            self.get_logger().fatal(
                "'gpio_chip' parametresi bos -- once karti kontrol edip "
                '(gpiodetect) dogru chip adini (ornek: gpiochip0) '
                'params dosyasina yazin.')
            raise RuntimeError('gpio_chip parametresi yapilandirilmadi')

        try:
            self.chip = gpiod.Chip(gpio_chip_name)
        except OSError as e:
            self.get_logger().fatal(f"GPIO chip acilamadi ({gpio_chip_name}): {e}")
            raise

        self.motor1 = GpioHBridgeMotor(
            self.chip,
            self.get_parameter('motor1_in1_line').value,
            self.get_parameter('motor1_in2_line').value,
            invert=self.get_parameter('motor1_invert').value)
        self.motor2 = GpioHBridgeMotor(
            self.chip,
            self.get_parameter('motor2_in1_line').value,
            self.get_parameter('motor2_in2_line').value,
            invert=self.get_parameter('motor2_invert').value)

        encoder_lines = [
            self.get_parameter('encoder1_a_line').value,
            self.get_parameter('encoder1_b_line').value,
            self.get_parameter('encoder2_a_line').value,
            self.get_parameter('encoder2_b_line').value,
        ]
        if all(line >= 0 for line in encoder_lines):
            self.encoder1 = QuadratureEncoder(
                self.chip,
                self.get_parameter('encoder1_a_line').value,
                self.get_parameter('encoder1_b_line').value,
                invert=self.get_parameter('encoder1_invert').value)
            self.encoder2 = QuadratureEncoder(
                self.chip,
                self.get_parameter('encoder2_a_line').value,
                self.get_parameter('encoder2_b_line').value,
                invert=self.get_parameter('encoder2_invert').value)
            self.encoders_enabled = True
        else:
            self.encoder1 = None
            self.encoder2 = None
            self.encoders_enabled = False
            self.get_logger().info(
                'Encoder pinleri tanimli degil; motor driver enkodersiz '
                '(open-loop) calisacak ve wheel odom yayinlamayacak.')

        self.last_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.odom_integrator = OdometryIntegrator()
        self.last_odom_time = self.get_clock().now()

        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_cb, 10)
        self.odom_pub = self.create_publisher(Odometry, 'wheel_odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None

        control_rate = self.get_parameter('control_rate_hz').value
        self.create_timer(1.0 / control_rate, self.control_loop)

        self.get_logger().info(
            f'Motor surucu basladi (GPIO/libgpiod): chip={gpio_chip_name} '
            f'wheel_separation={self.wheel_separation} m '
            f'wheel_radius={self.wheel_radius} m '
            f'ticks_per_rev={self.ticks_per_rev} '
            f'encoders_enabled={self.encoders_enabled}')

    def cmd_vel_cb(self, msg: Twist):
        self.last_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def control_loop(self):
        now = self.get_clock().now()
        elapsed = (now - self.last_cmd_time).nanoseconds / 1e9

        if elapsed > self.cmd_vel_timeout:
            left_pct, right_pct = 0.0, 0.0
        else:
            speeds = twist_to_wheel_speeds(
                self.last_cmd.linear.x, self.last_cmd.angular.z, self.wheel_separation)
            left_pct = wheel_speed_to_percent(speeds.left_mps, self.max_wheel_speed)
            right_pct = wheel_speed_to_percent(speeds.right_mps, self.max_wheel_speed)

        self.motor1.drive(left_pct)
        self.motor2.drive(right_pct)

        self._update_odometry(now)

    def _update_odometry(self, now: Time):
        if not self.encoders_enabled:
            return
        dt = (now - self.last_odom_time).nanoseconds / 1e9
        self.last_odom_time = now
        if dt <= 0.0:
            return

        left_ticks = self.encoder1.read_and_reset_ticks()
        right_ticks = self.encoder2.read_and_reset_ticks()

        left_distance = ticks_to_distance(left_ticks, self.ticks_per_rev, self.wheel_radius)
        right_distance = ticks_to_distance(right_ticks, self.ticks_per_rev, self.wheel_radius)

        left_mps = left_distance / dt
        right_mps = right_distance / dt
        twist = wheel_speeds_to_twist(left_mps, right_mps, self.wheel_separation)
        pose = self.odom_integrator.update(twist.linear_x, twist.angular_z, dt)

        stamp = now.to_msg()
        quat = quaternion_from_euler(0.0, 0.0, pose.theta)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.base_frame_id
        odom.pose.pose.position.x = pose.x
        odom.pose.pose.position.y = pose.y
        odom.pose.pose.orientation.x = quat[0]
        odom.pose.pose.orientation.y = quat[1]
        odom.pose.pose.orientation.z = quat[2]
        odom.pose.pose.orientation.w = quat[3]
        odom.twist.twist.linear.x = twist.linear_x
        odom.twist.twist.angular.z = twist.angular_z
        self.odom_pub.publish(odom)

        if self.tf_broadcaster is not None:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = stamp
            tf_msg.header.frame_id = self.odom_frame_id
            tf_msg.child_frame_id = self.base_frame_id
            tf_msg.transform.translation.x = pose.x
            tf_msg.transform.translation.y = pose.y
            tf_msg.transform.rotation.x = quat[0]
            tf_msg.transform.rotation.y = quat[1]
            tf_msg.transform.rotation.z = quat[2]
            tf_msg.transform.rotation.w = quat[3]
            self.tf_broadcaster.sendTransform(tf_msg)

    def destroy_node(self):
        try:
            self.motor1.stop()
            self.motor2.stop()
            self.motor1.release()
            self.motor2.release()
            if self.encoder1 is not None:
                self.encoder1.stop()
            if self.encoder2 is not None:
                self.encoder2.stop()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
