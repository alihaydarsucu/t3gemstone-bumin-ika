"""gemstone_ultrasonic: Harezmi kartindaki HC-SR04 benzeri ultrasonik
mesafe sensorlerini (trig/echo, libgpiod uzerinden) okuyup her biri icin
ayri bir sensor_msgs/Range topic'i yayinlayan node.

Harezmi/Deneyap pin haritasinda 2 ultrasonik slotu vardi:
  1. MSF: trig=D0(A13), echo=D1(A12)
  2. MSF: trig=D7, echo=D8 (Deneyap'ta cizgi sensoru/buzzer ile pin
     paylasiyordu; Gemstone GPIO'sunda bu kisitlama yok, kablolamaniza
     gore serbestce secebilirsiniz)

En az bir sensor (ultrasonicN_trig_line >= 0) yapilandirilmalidir, ikisi
de opsiyoneldir.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range

try:
    import gpiod
except ImportError:  # pragma: no cover - sadece Linux/karti disinda (ör. gelistirme makinesi)
    gpiod = None

from gemstone_ultrasonic.hc_sr04 import HcSr04Sensor


class UltrasonicNode(Node):

    def __init__(self):
        super().__init__('ultrasonic_node')

        self.declare_parameter('gpio_chip', '')
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('min_range', 0.02)
        self.declare_parameter('max_range', 4.0)
        self.declare_parameter('field_of_view', 0.26)

        self.declare_parameter('ultrasonic1_trig_line', -1)
        self.declare_parameter('ultrasonic1_echo_line', -1)
        self.declare_parameter('ultrasonic1_frame_id', 'ultrasonic1_link')
        self.declare_parameter('ultrasonic1_topic', 'ultrasonic1/range')

        self.declare_parameter('ultrasonic2_trig_line', -1)
        self.declare_parameter('ultrasonic2_echo_line', -1)
        self.declare_parameter('ultrasonic2_frame_id', 'ultrasonic2_link')
        self.declare_parameter('ultrasonic2_topic', 'ultrasonic2/range')

        self.min_range = self.get_parameter('min_range').value
        self.max_range = self.get_parameter('max_range').value
        self.field_of_view = self.get_parameter('field_of_view').value

        gpio_chip_name = self.get_parameter('gpio_chip').value
        if not gpio_chip_name:
            self.get_logger().fatal(
                "'gpio_chip' parametresi bos -- once karti kontrol edip "
                '(gpiodetect) dogru chip adini params dosyasina yazin.')
            raise RuntimeError('gpio_chip parametresi yapilandirilmadi')

        try:
            self.chip = gpiod.Chip(gpio_chip_name)
        except OSError as e:
            self.get_logger().fatal(f"GPIO chip acilamadi ({gpio_chip_name}): {e}")
            raise

        self.sensors = []  # [(HcSr04Sensor, frame_id, publisher), ...]
        self._maybe_add_sensor(1)
        self._maybe_add_sensor(2)

        if not self.sensors:
            self.get_logger().fatal(
                'Hicbir ultrasonik sensor yapilandirilmadi '
                '(ultrasonic1/2_trig_line hepsi -1).')
            raise RuntimeError('En az bir ultrasonik sensor yapilandirilmali')

        rate = self.get_parameter('publish_rate_hz').value
        self.create_timer(1.0 / rate, self._measure_and_publish_all)

        self.get_logger().info(
            f'{len(self.sensors)} ultrasonik sensor ile basladi (chip={gpio_chip_name})')

    def _maybe_add_sensor(self, index: int):
        trig = self.get_parameter(f'ultrasonic{index}_trig_line').value
        echo = self.get_parameter(f'ultrasonic{index}_echo_line').value
        if trig < 0 or echo < 0:
            return
        frame_id = self.get_parameter(f'ultrasonic{index}_frame_id').value
        topic = self.get_parameter(f'ultrasonic{index}_topic').value
        sensor = HcSr04Sensor(self.chip, trig, echo)
        publisher = self.create_publisher(Range, topic, 10)
        self.sensors.append((sensor, frame_id, publisher))

    def _measure_and_publish_all(self):
        stamp = self.get_clock().now().to_msg()
        for sensor, frame_id, publisher in self.sensors:
            distance = sensor.measure_distance()

            msg = Range()
            msg.header.stamp = stamp
            msg.header.frame_id = frame_id
            msg.radiation_type = Range.ULTRASOUND
            msg.field_of_view = self.field_of_view
            msg.min_range = self.min_range
            msg.max_range = self.max_range
            # Zaman asimi: engel yok ya da menzil disi -- REP-117'ye gore
            # menzil disini max_range+ ile temsil etmek yerine +inf kullanmak
            # da yaygin bir tercih; burada max_range'i asan bir deger
            # (max_range'in kendisi) yerine +inf ile "gecerli olcum degil"
            # ayrimini nettir.
            msg.range = float('inf') if distance is None else max(
                self.min_range, min(self.max_range, distance))
            publisher.publish(msg)

    def destroy_node(self):
        for sensor, _, _ in self.sensors:
            try:
                sensor.release()
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
