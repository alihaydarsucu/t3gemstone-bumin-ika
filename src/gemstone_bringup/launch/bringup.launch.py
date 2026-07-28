from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    imu_spi_device = LaunchConfiguration("imu_spi_device")
    imu_frame_id = LaunchConfiguration("imu_frame_id")
    imu_publish_rate_hz = LaunchConfiguration("imu_publish_rate_hz")
    lidar_serial_port = LaunchConfiguration("lidar_serial_port")
    lidar_serial_baudrate = LaunchConfiguration("lidar_serial_baudrate")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "imu_spi_device",
                default_value="/dev/spidev0.3",
            ),
            DeclareLaunchArgument("imu_frame_id", default_value="icm20948_link"),
            DeclareLaunchArgument(
                "imu_publish_rate_hz",
                default_value="100.0",
            ),
            DeclareLaunchArgument(
                "lidar_serial_port",
                default_value="/dev/ttyUSB0",
            ),
            DeclareLaunchArgument(
                "lidar_serial_baudrate",
                default_value="115200",
            ),
            Node(
                package="gemstone_bringup",
                executable="imu_node",
                name="gemstone_imu",
                output="screen",
                parameters=[
                    {
                        "spi_device": imu_spi_device,
                        "frame_id": imu_frame_id,
                        "publish_rate_hz": ParameterValue(
                            imu_publish_rate_hz, value_type=float
                        ),
                    }
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("sllidar_ros2"),
                            "launch",
                            "view_sllidar_a1_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "channel_type": "serial",
                    "serial_port": lidar_serial_port,
                    "serial_baudrate": lidar_serial_baudrate,
                }.items(),
            ),
        ]
    )
