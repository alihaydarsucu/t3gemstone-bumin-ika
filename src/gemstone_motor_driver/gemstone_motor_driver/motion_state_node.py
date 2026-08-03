"""IMU + istege bagli wheel odom birlestiren hareket durumu node'u.

Bu node'un amaci:
- IMU'dan roll/pitch/yaw takip etmek
- Encoder varsa wheel odom ile yaw'i daha karali hale getirmek
- Encoder yoksa IMU-only modda calisip en azindan aci takibi saglamak

Kural basit: wheel odom geliyorsa onu kullan, gelmiyorsa IMU ile devam et.
"""

import rclpy
from geometry_msgs.msg import Quaternion
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Bool, Float64
from tf_transformations import euler_from_quaternion, quaternion_from_euler

from gemstone_motor_driver.motion_state import (
    accel_to_roll_pitch,
    average_angles,
    wrap_angle,
)


def _quat_to_euler(msg_quat: Quaternion) -> tuple[float, float, float]:
    return euler_from_quaternion([
        msg_quat.x,
        msg_quat.y,
        msg_quat.z,
        msg_quat.w,
    ])


class MotionStateNode(Node):

    def __init__(self):
        super().__init__('motion_state_node')

        self.declare_parameter('imu_topic', 'imu/data')
        self.declare_parameter('wheel_odom_topic', 'wheel_odom')
        self.declare_parameter('output_odom_topic', 'motion_state/odom')
        self.declare_parameter('output_yaw_topic', 'motion_state/yaw')
        self.declare_parameter('output_encoder_available_topic', 'motion_state/encoder_available')
        self.declare_parameter('wheel_odom_timeout', 0.5)
        self.declare_parameter('imu_yaw_weight', 0.7)
        self.declare_parameter('frame_id', 'odom')
        self.declare_parameter('child_frame_id', 'base_link')

        self.imu_topic = self.get_parameter('imu_topic').value
        self.wheel_odom_topic = self.get_parameter('wheel_odom_topic').value
        self.output_odom_topic = self.get_parameter('output_odom_topic').value
        self.output_yaw_topic = self.get_parameter('output_yaw_topic').value
        self.output_encoder_available_topic = self.get_parameter(
            'output_encoder_available_topic').value
        self.wheel_odom_timeout = self.get_parameter('wheel_odom_timeout').value
        self.imu_yaw_weight = self.get_parameter('imu_yaw_weight').value
        self.frame_id = self.get_parameter('frame_id').value
        self.child_frame_id = self.get_parameter('child_frame_id').value

        if not 0.0 <= self.imu_yaw_weight <= 1.0:
            raise ValueError('imu_yaw_weight 0.0 ile 1.0 arasinda olmali')

        self._last_imu_time = None
        self._last_wheel_time = None
        self._latest_wheel_odom = None

        self._roll = 0.0
        self._pitch = 0.0
        self._yaw = 0.0
        self._x = 0.0
        self._y = 0.0
        self._wheel_active = False

        self.create_subscription(Imu, self.imu_topic, self.imu_cb, 20)
        self.create_subscription(Odometry, self.wheel_odom_topic, self.wheel_odom_cb, 20)

        self.odom_pub = self.create_publisher(Odometry, self.output_odom_topic, 20)
        self.yaw_pub = self.create_publisher(Float64, self.output_yaw_topic, 20)
        self.encoder_available_pub = self.create_publisher(
            Bool, self.output_encoder_available_topic, 10)

        self.get_logger().info(
            f'Motion state node basladi: imu={self.imu_topic}, '
            f'wheel_odom={self.wheel_odom_topic}, timeout={self.wheel_odom_timeout:.2f}s, '
            f'imu_yaw_weight={self.imu_yaw_weight:.2f}')

    def wheel_odom_cb(self, msg: Odometry):
        self._latest_wheel_odom = msg
        self._last_wheel_time = self.get_clock().now()
        self._wheel_active = True

    def imu_cb(self, msg: Imu):
        now = self.get_clock().now()
        if self._last_imu_time is None:
            dt = 0.0
        else:
            dt = (now - self._last_imu_time).nanoseconds / 1e9
        self._last_imu_time = now

        if msg.orientation_covariance[0] >= 0.0:
            roll, pitch, imu_yaw = _quat_to_euler(msg.orientation)
        else:
            roll, pitch = accel_to_roll_pitch(
                msg.linear_acceleration.x,
                msg.linear_acceleration.y,
                msg.linear_acceleration.z,
            )
            if dt > 0.0:
                self._yaw = wrap_angle(self._yaw + msg.angular_velocity.z * dt)
            imu_yaw = self._yaw

        encoder_active = self._wheel_odom_is_fresh(now)
        if encoder_active and self._latest_wheel_odom is not None:
            wheel_roll, wheel_pitch, wheel_yaw = _quat_to_euler(
                self._latest_wheel_odom.pose.pose.orientation)
            fused_yaw = average_angles(imu_yaw, wheel_yaw, primary_weight=self.imu_yaw_weight)
            self._x = self._latest_wheel_odom.pose.pose.position.x
            self._y = self._latest_wheel_odom.pose.pose.position.y
            self._yaw = fused_yaw
            self._roll = roll if abs(roll) > 1e-9 else wheel_roll
            self._pitch = pitch if abs(pitch) > 1e-9 else wheel_pitch
        else:
            fused_yaw = imu_yaw
            self._yaw = fused_yaw
            self._roll = roll
            self._pitch = pitch

        quat = quaternion_from_euler(self._roll, self._pitch, self._yaw)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation.x = quat[0]
        odom.pose.pose.orientation.y = quat[1]
        odom.pose.pose.orientation.z = quat[2]
        odom.pose.pose.orientation.w = quat[3]

        if encoder_active and self._latest_wheel_odom is not None:
            odom.twist.twist.linear.x = self._latest_wheel_odom.twist.twist.linear.x
            odom.twist.twist.angular.z = self._latest_wheel_odom.twist.twist.angular.z
            self._set_covariance(odom, pos_cov=0.02, yaw_cov=0.05)
        else:
            odom.twist.twist.linear.x = 0.0
            odom.twist.twist.angular.z = msg.angular_velocity.z
            self._set_covariance(odom, pos_cov=9.0, yaw_cov=0.20)

        self.odom_pub.publish(odom)

        yaw_msg = Float64()
        yaw_msg.data = self._yaw
        self.yaw_pub.publish(yaw_msg)

        encoder_msg = Bool()
        encoder_msg.data = encoder_active
        self.encoder_available_pub.publish(encoder_msg)

    def _wheel_odom_is_fresh(self, now):
        if self._last_wheel_time is None:
            self._wheel_active = False
            return False
        age = (now - self._last_wheel_time).nanoseconds / 1e9
        self._wheel_active = age <= self.wheel_odom_timeout
        return self._wheel_active

    def _set_covariance(self, odom: Odometry, pos_cov: float, yaw_cov: float):
        for i in range(36):
            odom.pose.covariance[i] = 0.0
            odom.twist.covariance[i] = 0.0
        odom.pose.covariance[0] = pos_cov
        odom.pose.covariance[7] = pos_cov
        odom.pose.covariance[35] = yaw_cov
        odom.twist.covariance[0] = pos_cov
        odom.twist.covariance[35] = yaw_cov


def main(args=None):
    rclpy.init(args=args)
    node = MotionStateNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
