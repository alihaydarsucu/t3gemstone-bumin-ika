import math
import re
import struct
import time
from typing import Tuple

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

try:
    import spidev
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    spidev = None
    _SPIDEV_IMPORT_ERROR = exc
else:
    _SPIDEV_IMPORT_ERROR = None


ICM20948_WHO_AM_I = 0x00
ICM20948_PWR_MGMT_1 = 0x06
ICM20948_PWR_MGMT_2 = 0x07
ICM20948_GYRO_SMPLRT_DIV = 0x00
ICM20948_GYRO_CONFIG_1 = 0x01
ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10
ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11
ICM20948_ACCEL_CONFIG = 0x14
ICM20948_ACCEL_CONFIG_2 = 0x15
ICM20948_ACCEL_XOUT_H = 0x2D
ICM20948_GYRO_XOUT_H = 0x33
ICM20948_TEMP_OUT_H = 0x39
ICM20948_REG_BANK_SEL = 0x7F

ICM20948_DEVICE_ID = 0xEA


def _parse_spi_device(device_path: str) -> Tuple[int, int]:
    match = re.fullmatch(r"/dev/spidev(\d+)\.(\d+)", device_path)
    if not match:
        raise ValueError(
            f"Unsupported SPI device path '{device_path}'. Expected /dev/spidev<BUS>.<DEVICE>."
        )
    return int(match.group(1)), int(match.group(2))


class ICM20948:
    def __init__(self, device_path: str):
        if spidev is None:
            raise RuntimeError(
                "python3-spidev is required to use the Gemstone IMU node."
            ) from _SPIDEV_IMPORT_ERROR

        bus, device = _parse_spi_device(device_path)
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = 3_000_000
        self._spi.mode = 0b00
        self._spi.bits_per_word = 8
        self._bank = None

    def close(self):
        self._spi.close()

    def _select_bank(self, bank: int):
        if self._bank == bank:
            return
        self._spi.xfer2([ICM20948_REG_BANK_SEL, bank << 4])
        self._bank = bank

    def write_reg(self, bank: int, reg: int, value: int):
        self._select_bank(bank)
        self._spi.xfer2([reg & 0x7F, value & 0xFF])

    def read_reg(self, bank: int, reg: int) -> int:
        self._select_bank(bank)
        response = self._spi.xfer2([0x80 | (reg & 0x7F), 0x00])
        return response[1]

    def read_block(self, bank: int, start_reg: int, length: int) -> bytes:
        self._select_bank(bank)
        response = self._spi.xfer2([0x80 | (start_reg & 0x7F)] + [0x00] * length)
        return bytes(response[1:])

    def initialize(self):
        self.write_reg(0, ICM20948_PWR_MGMT_1, 0x80)
        time.sleep(0.1)
        self.write_reg(0, ICM20948_PWR_MGMT_1, 0x01)
        self.write_reg(0, ICM20948_PWR_MGMT_2, 0x00)
        time.sleep(0.05)

        # Use full-scale ranges that fit common mobile robot mounting.
        # Gyro: +/- 2000 dps, Accel: +/- 8 g.
        self.write_reg(2, ICM20948_GYRO_SMPLRT_DIV, 0x00)
        self.write_reg(2, ICM20948_GYRO_CONFIG_1, 0x06)
        self.write_reg(2, ICM20948_ACCEL_SMPLRT_DIV_1, 0x00)
        self.write_reg(2, ICM20948_ACCEL_SMPLRT_DIV_2, 0x00)
        self.write_reg(2, ICM20948_ACCEL_CONFIG, 0x04)
        self.write_reg(2, ICM20948_ACCEL_CONFIG_2, 0x00)

        who_am_i = self.read_reg(0, ICM20948_WHO_AM_I)
        if who_am_i != ICM20948_DEVICE_ID:
            raise RuntimeError(
                f"ICM-20948 WHO_AM_I mismatch: expected 0x{ICM20948_DEVICE_ID:02X}, got 0x{who_am_i:02X}"
            )

    def read_measurement(self):
        raw = self.read_block(0, ICM20948_ACCEL_XOUT_H, 14)
        ax, ay, az, temp, gx, gy, gz = struct.unpack(">hhhhhhh", raw)
        return ax, ay, az, temp, gx, gy, gz


class GemstoneImuNode(Node):
    def __init__(self):
        super().__init__("gemstone_imu")

        self.declare_parameter("spi_device", "/dev/spidev0.3")
        self.declare_parameter("frame_id", "icm20948_link")
        self.declare_parameter("publish_rate_hz", 100.0)
        self.declare_parameter("linear_accel_stddev", 0.02)
        self.declare_parameter("angular_velocity_stddev", 0.01)

        self._frame_id = self.get_parameter("frame_id").value
        self._publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._accel_stddev = float(self.get_parameter("linear_accel_stddev").value)
        self._gyro_stddev = float(self.get_parameter("angular_velocity_stddev").value)
        self._accel_sensitivity = 4096.0  # LSB/g for +/-8g
        self._gyro_sensitivity = 16.4  # LSB/dps for +/-2000 dps
        self._gravity = 9.80665

        spi_device = self.get_parameter("spi_device").value
        self._imu = ICM20948(spi_device)
        self._imu.initialize()

        self._publisher = self.create_publisher(Imu, "/gemstone/imu/data", 10)
        period = 1.0 / max(self._publish_rate_hz, 1.0)
        self._timer = self.create_timer(period, self._publish_imu)

        who_am_i = self._imu.read_reg(0, ICM20948_WHO_AM_I)
        self.get_logger().info(
            f"ICM-20948 ready on {spi_device} (WHO_AM_I=0x{who_am_i:02X}), publishing /gemstone/imu/data"
        )

    def destroy_node(self):
        try:
            self._imu.close()
        except Exception:
            pass
        return super().destroy_node()

    def _publish_imu(self):
        try:
            ax, ay, az, temp_raw, gx, gy, gz = self._imu.read_measurement()
        except OSError as exc:
            self.get_logger().error(f"IMU read failed: {exc}")
            return
        except RuntimeError as exc:
            self.get_logger().error(f"IMU read failed: {exc}")
            return

        accel_scale = self._gravity / self._accel_sensitivity
        gyro_scale = (math.pi / 180.0) / self._gyro_sensitivity
        temperature_c = (temp_raw / 333.87) + 21.0

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.orientation_covariance[0] = -1.0
        msg.angular_velocity.x = gx * gyro_scale
        msg.angular_velocity.y = gy * gyro_scale
        msg.angular_velocity.z = gz * gyro_scale
        msg.linear_acceleration.x = ax * accel_scale
        msg.linear_acceleration.y = ay * accel_scale
        msg.linear_acceleration.z = az * accel_scale

        covariance_accel = self._accel_stddev ** 2
        covariance_gyro = self._gyro_stddev ** 2
        msg.linear_acceleration_covariance[0] = covariance_accel
        msg.linear_acceleration_covariance[4] = covariance_accel
        msg.linear_acceleration_covariance[8] = covariance_accel
        msg.angular_velocity_covariance[0] = covariance_gyro
        msg.angular_velocity_covariance[4] = covariance_gyro
        msg.angular_velocity_covariance[8] = covariance_gyro

        self._publisher.publish(msg)
        self.get_logger().debug(
            f"imu accel=({msg.linear_acceleration.x:.3f}, {msg.linear_acceleration.y:.3f}, {msg.linear_acceleration.z:.3f}) "
            f"gyro=({msg.angular_velocity.x:.3f}, {msg.angular_velocity.y:.3f}, {msg.angular_velocity.z:.3f}) "
            f"temp={temperature_c:.2f}C"
        )


def main(args=None):
    rclpy.init(args=args)
    node = GemstoneImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Gemstone IMU node stopped.")
    finally:
        node.destroy_node()
        rclpy.shutdown()
