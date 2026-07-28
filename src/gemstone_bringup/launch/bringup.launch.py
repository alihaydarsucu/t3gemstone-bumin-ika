from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_file = LaunchConfiguration("config_file")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("gemstone_bringup"), "config", "bringup.yaml"]
                ),
            ),
            Node(
                package="gemstone_bringup",
                executable="bringup_node",
                name="gemstone_bringup",
                output="screen",
                parameters=[config_file],
            ),
        ]
    )
