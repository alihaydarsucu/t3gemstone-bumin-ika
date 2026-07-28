"""gemstone_image_proc: goruntu isleme icin iskelet (placeholder) node.

Su an sadece camera/image_raw'i dinleyip kac FPS geldigini loglar ve
degistirmeden camera/image_processed'e yeniden yayinlar. Serit takibi,
engel/isaret tespiti gibi gercek gorevler process_frame() icine eklenecek
sekilde tasarlanmistir -- OpenCV/cv_bridge donusumu zaten burada hazir.
"""

from cv_bridge import CvBridge

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class ImageProcessingNode(Node):

    def __init__(self):
        super().__init__('image_processing_node')

        self.declare_parameter('input_topic', 'camera/image_raw')
        self.declare_parameter('output_topic', 'camera/image_processed')
        self.declare_parameter('log_fps_every_n_frames', 60)

        self.bridge = CvBridge()
        self.frame_count = 0
        self.log_every_n = self.get_parameter('log_fps_every_n_frames').value
        self._last_log_time = self.get_clock().now()

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        self.publisher = self.create_publisher(Image, output_topic, 10)
        self.create_subscription(Image, input_topic, self.image_cb, 10)

        self.get_logger().info(
            f'Goruntu isleme node u basladi: {input_topic} -> {output_topic}')

    def process_frame(self, frame):
        """Gercek goruntu isleme mantigi buraya eklenecek (serit takibi,
        renk/kontur bazli engel tespiti, nesne tanima vb.). `frame` bir
        OpenCV/numpy BGR8 goruntusudur (cv2.cvtColor, cv2.Canny, vb.
        dogrudan kullanilabilir). Su an frame'i oldugu gibi geri donduruyor.
        """
        return frame

    def image_cb(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        processed = self.process_frame(frame)

        out_msg = self.bridge.cv2_to_imgmsg(processed, encoding='bgr8')
        out_msg.header = msg.header
        self.publisher.publish(out_msg)

        self.frame_count += 1
        if self.frame_count % self.log_every_n == 0:
            now = self.get_clock().now()
            elapsed = (now - self._last_log_time).nanoseconds / 1e9
            fps = self.log_every_n / elapsed if elapsed > 0 else 0.0
            self.get_logger().info(f'~{fps:.1f} FPS ({self.frame_count} kare islendi)')
            self._last_log_time = now

def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessingNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
