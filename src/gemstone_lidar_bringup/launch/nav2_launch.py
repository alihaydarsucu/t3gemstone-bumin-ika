"""gemstone_lidar_bringup icin ozel Nav2 (navigation) launch dosyasi.

Neden nav2_bringup'un kendi `bringup_launch.py` / `navigation_launch.py`
dosyasini oldugu gibi kullanmiyoruz?

  - `bringup_launch.py`, `slam:=false` oldugunda AMCL + map_server baslatir.
    Biz SLAM'i kendi slam_toolbox instance'imizla (mapping modu) yapiyoruz,
    AMCL'ye ve hazir haritaya ihtiyacimiz yok.
  - Stok `navigation_launch.py` velocity_smoother ciktisini `/cmd_vel`'a
    remap eder; bizim `obstacle_avoidance_node`'umuz da `/cmd_vel`'a yazar.
    Iki publisher cakismasin diye Nav2'nin tum hiz ciktilarini (controller
    + recovery/behavior) `cmd_vel_nav` topic'ine baglariz; guvenlik katmani
    oradan `/cmd_vel`'a gecer.

Bu dosya sadece navigasyon sunucularini baslatir (controller, planner,
behavior/recovery, bt_navigator, smoother, waypoint_follower + lifecycle
manager). SLAM ve harita ayri ele alinir.

Kullanim:
  ros2 launch gemstone_lidar_bringup nav2_launch.py \
      params_file:=<nav2_params.yaml> use_sim_time:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('gemstone_lidar_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    odom_topic = LaunchConfiguration('odom_topic')

    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'waypoint_follower',
    ]

    remappings = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
    ]
    # Nav2 hiz ciktilarini guvenlik katmaninin giris topic'ine bagla.
    nav_remappings = remappings + [('cmd_vel', cmd_vel_topic)]

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false')
    declare_autostart = DeclareLaunchArgument(
        'autostart', default_value='true')
    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_share, 'params', 'nav2_params.yaml'))
    declare_cmd_vel_topic = DeclareLaunchArgument(
        'cmd_vel_topic', default_value='cmd_vel_nav')
    declare_odom_topic = DeclareLaunchArgument(
        'odom_topic', default_value='/odom_rf2o')

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=nav_remappings,
    )

    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=remappings,
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=remappings,
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=nav_remappings,
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time,
                                  'odom_topic': odom_topic}],
        remappings=remappings,
    )

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=remappings,
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'node_names': lifecycle_nodes,
        }],
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_autostart,
        declare_params_file,
        declare_cmd_vel_topic,
        declare_odom_topic,
        controller_server,
        smoother_server,
        planner_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        lifecycle_manager,
    ])
