"""gcs_bringup: tarayicida calisan GCS (Ground Control Station) web launch'i.

Robot tarafindan (gemstone_sim / auto_mapping) bagimsiz olarak 3 web
bilesenini ayaga kaldirir:

  1. rosbridge_websocket  -> ws://localhost:9090  (ROS topic/servis, roslib.js)
  2. web_video_server     -> http://localhost:8080/stream?topic=/camera/image_raw
  3. http.server (statik) -> http://localhost:8000  (gcs/ web arayuzu)

Bu launch robot tarafini icermez: gercek hayatta GCS ayri bir bilgisayarda
calisir ve robotla ROS graph uzerinden (ROS_DOMAIN_ID / DDS) haberlesir.
Robot tarafini ayri baslatmak icin:

  ros2 launch gemstone_frontier_explorer auto_mapping.launch.py \
      enable_rviz:=true world_file:=<path>  # sim'de robot tarafi

Kullanim (sim, ayri terminal):
  # Terminal 1 - robot tarafi (sim + Nav2 + kesif + RViz):
  ros2 launch gemstone_frontier_explorer auto_mapping.launch.py

  # Terminal 2 - GCS web tarafi:
  ros2 launch gemstone_gcs gcs_bringup.launch.py
  # tarayicida http://localhost:8000 ac, 'Baglan' de.

Not: web_video_server MJPEG akisi web_video_server paketinin node'u ile
calisir; image_proc senkronize GOP yapilandirmasi kullanilmaz (raw JPEG).
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    web_root = LaunchConfiguration(
        'web_root',
        default='/ros_ws/src/t3gemstone-bumin-ika/gcs')
    rosbridge_port = LaunchConfiguration('rosbridge_port', default='9090')
    video_port = LaunchConfiguration('video_port', default='8080')
    web_port = LaunchConfiguration('web_port', default='8000')

    declare_web_root = DeclareLaunchArgument(
        'web_root',
        default_value='/ros_ws/src/t3gemstone-bumin-ika/gcs',
        description='Web arayüzünün dizini (http.server root).')
    declare_rosbridge_port = DeclareLaunchArgument(
        'rosbridge_port', default_value='9090')
    declare_video_port = DeclareLaunchArgument(
        'video_port', default_value='8080')
    declare_web_port = DeclareLaunchArgument(
        'web_port', default_value='8000')

    rosbridge_websocket = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{
            'port': rosbridge_port,
            'address': '0.0.0.0',
            'url_path': '/',
            'retry_startup_delay': 5.0,
            'fragment_timeout': 600,
            'delay_between_messages': 0.0,
            'max_message_size': 10000000,
            'unregister_timeout': 10.0,
            'use_compression': False,
            'websocket_ping_interval': 0.0,
            'websocket_ping_timeout': 30.0,
            'call_services_in_new_thread': False,
            'default_call_service_timeout': 0.0,
            'send_action_goals_in_new_thread': False,
        }],
    )

    rosapi = Node(
        package='rosapi',
        executable='rosapi_node',
        name='rosapi',
        output='screen',
        parameters=[{'topics_glob': '', 'services_glob': '', 'params_glob': ''}],
    )

    web_video_server = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{'port': video_port}],
    )

    web_static = ExecuteProcess(
        cmd=['python3', '-m', 'http.server', web_port,
             '--bind', '0.0.0.0', '--directory', web_root],
        output='screen',
    )

    return LaunchDescription([
        declare_web_root,
        declare_rosbridge_port,
        declare_video_port,
        declare_web_port,
        rosbridge_websocket,
        rosapi,
        web_video_server,
        web_static,
    ])
