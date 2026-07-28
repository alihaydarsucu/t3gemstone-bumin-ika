import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class BringupNode(Node):
    def __init__(self):
        super().__init__("gemstone_bringup")

        self.declare_parameter("enable_camera", True)
        self.declare_parameter("enable_lidar", True)
        self.declare_parameter("enable_motor", True)
        self.declare_parameter("status_topic", "/gemstone/system/status")

        topic_name = self.get_parameter("status_topic").get_parameter_value().string_value
        self._status_pub = self.create_publisher(String, topic_name, 10)
        self._timer = self.create_timer(1.0, self._publish_status)

        self.get_logger().info("Gemstone bringup node started.")
        self.get_logger().info(
            "camera=%s lidar=%s motor=%s"
            % (
                self.get_parameter("enable_camera").value,
                self.get_parameter("enable_lidar").value,
                self.get_parameter("enable_motor").value,
            )
        )

    def _publish_status(self):
        payload = {
            "camera": bool(self.get_parameter("enable_camera").value),
            "lidar": bool(self.get_parameter("enable_lidar").value),
            "motor": bool(self.get_parameter("enable_motor").value),
        }
        message = String()
        message.data = json.dumps(payload, ensure_ascii=False)
        self._status_pub.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = BringupNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Gemstone bringup node stopped.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

