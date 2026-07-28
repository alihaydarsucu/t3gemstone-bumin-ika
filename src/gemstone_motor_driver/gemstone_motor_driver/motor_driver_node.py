"""gemstone_motor_driver: /cmd_vel (geometry_msgs/Twist) komutunu
diferansiyel surus kinematigiyle sol/sag teker hizina cevirip UART
uzerinden harici motor surucu karta gonderen node.

Guvenlik: /cmd_vel belirli bir sure (cmd_vel_timeout) icinde gelmezse
node otomatik olarak DUR komutu gonderir (watchdog). Gonderim sabit bir
control_rate_hz frekansinda yapilir; cmd_vel callback'i sadece son
komutu saklar, seri porta tek yerden (zamanlayici) yazilir.
"""

import serial

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus

from gemstone_motor_driver.differential_drive import (
    twist_to_wheel_speeds,
    wheel_speed_to_percent,
)
from gemstone_motor_driver.protocol import encode_speed_command, encode_stop_command


class MotorDriverNode(Node):

    def __init__(self):
        super().__init__('motor_driver_node')

        self.declare_parameter('serial_port', '/dev/ttyS0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('wheel_separation', 0.30)
        self.declare_parameter('max_wheel_speed', 1.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)
        self.declare_parameter('control_rate_hz', 20.0)

        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.max_wheel_speed = self.get_parameter('max_wheel_speed').value
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').value

        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value

        try:
            self.ser = serial.Serial(port, baud, timeout=0.05)
        except serial.SerialException as e:
            self.get_logger().fatal(f'Motor surucu seri port acilamadi ({port}): {e}')
            raise

        self.last_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.consecutive_write_failures = 0

        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_cb, 10)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)

        control_rate = self.get_parameter('control_rate_hz').value
        self.create_timer(1.0 / control_rate, self.control_loop)

        self.get_logger().info(
            f'Motor surucu basladi: port={port} baud={baud} '
            f'wheel_separation={self.wheel_separation} m max_wheel_speed={self.max_wheel_speed} m/s')

    def cmd_vel_cb(self, msg: Twist):
        self.last_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def control_loop(self):
        elapsed = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9

        if elapsed > self.cmd_vel_timeout:
            frame = encode_stop_command()
            if elapsed < self.cmd_vel_timeout + (1.0 / 20.0):
                # Sadece esigi yeni astigimizda bir kere uyar, spam yapma.
                self.get_logger().warn(
                    f'/cmd_vel {self.cmd_vel_timeout:.2f}s icinde gelmedi, motorlar durduruluyor.')
        else:
            speeds = twist_to_wheel_speeds(
                self.last_cmd.linear.x, self.last_cmd.angular.z, self.wheel_separation)
            left_pct = wheel_speed_to_percent(speeds.left_mps, self.max_wheel_speed)
            right_pct = wheel_speed_to_percent(speeds.right_mps, self.max_wheel_speed)
            frame = encode_speed_command(left_pct, right_pct)

        self._write_frame(frame)

    def _write_frame(self, frame: bytes):
        try:
            self.ser.write(frame)
            self.consecutive_write_failures = 0
        except serial.SerialException as e:
            self.consecutive_write_failures += 1
            self.get_logger().warn(f'Motor surucuye yazma hatasi: {e}', throttle_duration_sec=2.0)
        self._publish_diagnostics()

    def _publish_diagnostics(self):
        status = DiagnosticStatus()
        status.name = 'gemstone_motor_driver: uart_link'
        status.hardware_id = self.get_parameter('serial_port').value
        if self.consecutive_write_failures == 0:
            status.level = DiagnosticStatus.OK
            status.message = 'Seri port yazimi calisiyor'
        elif self.consecutive_write_failures < 10:
            status.level = DiagnosticStatus.WARN
            status.message = 'Ardisik yazma hatasi'
        else:
            status.level = DiagnosticStatus.ERROR
            status.message = 'Seri port yazimi surekli basarisiz'

        array = DiagnosticArray()
        array.header.stamp = self.get_clock().now().to_msg()
        array.status.append(status)
        self.diag_pub.publish(array)

    def destroy_node(self):
        try:
            self._write_frame(encode_stop_command())
            self.ser.close()
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
