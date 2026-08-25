"""RPLIDAR A1M8'in kendi taban kartindaki motor sürücüsünü (Q14) besleyen
CTRL_MOTO hattina sabit duty cycle'da PWM veren kucuk node.

Lidar artik orijinal USB adaptor karti uzerinden degil, dogrudan Gemstone'un
GPIO/UART'i ve bu PWM hatti uzerinden calisiyor (bkz. docs/09-bilinen-sorunlar
-ve-cozumler.md). %100 duty cycle'da motor akiminin ürettigi elektriksel
gurultu TX/RX haberlesmesini bozuyor; sahada test edilip dogrulanmis calisan
deger %85 (bkz. lidar_motor_pwm_params.yaml) -- 100'e yaklastirmayin.
"""

import rclpy
from rclpy.node import Node

from gemstone_motor_driver.sysfs_pwm import SysfsPwm


class LidarMotorPwmNode(Node):

    def __init__(self):
        super().__init__('lidar_motor_pwm_node')

        self.declare_parameter('pwm_chip', 3)
        self.declare_parameter('pwm_channel', 0)
        self.declare_parameter('period_ns', 1_000_000)
        self.declare_parameter('duty_percent', 85.0)

        chip = self.get_parameter('pwm_chip').value
        channel = self.get_parameter('pwm_channel').value
        period_ns = self.get_parameter('period_ns').value
        duty_percent = float(self.get_parameter('duty_percent').value)

        self._pwm = SysfsPwm(chip, channel, period_ns=period_ns)
        self._pwm.set_duty_percent(duty_percent)
        self.get_logger().info(
            f'lidar motor PWM etkin: pwmchip{chip}/pwm{channel}, '
            f'duty=%{duty_percent:.1f}')

    def destroy_node(self):
        self._pwm.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = LidarMotorPwmNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
