"""auto_mapping: otonom oda kesif + harita cikarma launch'i.

Gazebo sim ortaminda tam otonom haritalama akisini baslatir:

  1. gemstone_sim sim_bringup   -> Gazebo + robot + motion_state +
                                   obstacle_avoidance (guvenlik katmani).
                                   Eski reaktif exploration_demo_node
                                   devre disi (enable_exploration_demo:=false),
                                   cunku frontier_explorer_node da
                                   cmd_vel_nav'a yazar.
  2. gemstone_lidar_bringup     -> slam_toolbox (mapping) + Nav2 (nav2_launch)
                                   + odometry. Sim'de /odom (Gazebo) kullanilir,
                                   rf2o kapali, rplidar kapali.
  3. frontier_explorer_node     -> /map + tf ile frontier kesfi, Nav2 hedefleri.

Hedef akisi:
  Nav2 (cmd_vel_nav) -> obstacle_avoidance_node -> /cmd_vel -> diff_drive.

Kullanim (sim):
  ros2 launch gemstone_frontier_explorer auto_mapping.launch.py
  # sonra GCS veya rqt uzerinden:
  #   ros2 service call /exploration/start std_srvs/srv/Trigger "{}"
  #   ros2 service call /exploration/save_map std_srvs/srv/Trigger "{}"
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_path(pkg, file_name):
    return os.path.join(
        get_package_share_directory(pkg), 'launch', file_name)


def generate_launch_description():
    explorer_share = get_package_share_directory('gemstone_frontier_explorer')
    lidar_share = get_package_share_directory('gemstone_lidar_bringup')

    explorer_params = os.path.join(
        explorer_share, 'params', 'frontier_explorer.yaml')
    nav2_params = os.path.join(lidar_share, 'params', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_rviz = LaunchConfiguration('enable_rviz')
    enable_gui = LaunchConfiguration('enable_gui')
    world_file = LaunchConfiguration(
        'world_file',
        default=os.path.join(
            get_package_share_directory('gemstone_sim'),
            'worlds', 'house.world'))

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true')
    declare_enable_rviz = DeclareLaunchArgument(
        'enable_rviz', default_value='true')
    declare_enable_gui = DeclareLaunchArgument(
        'enable_gui', default_value='true')
    declare_real_time_factor = DeclareLaunchArgument(
        'real_time_factor', default_value='1.0',
        description='Gazebo gercek zaman carpani.')
    declare_world_file = DeclareLaunchArgument(
        'world_file',
        default_value=os.path.join(
            get_package_share_directory('gemstone_sim'),
            'worlds', 'house.world'),
        description='Gazebo dünya dosyasi (mutlak yol). Varsayilan: house.world.')
    declare_x_pose = DeclareLaunchArgument('x_pose', default_value='-3.0')
    declare_y_pose = DeclareLaunchArgument('y_pose', default_value='2.0')
    declare_z_pose = DeclareLaunchArgument('z_pose', default_value='0.075')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='1.5708')

    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_launch_path('gemstone_sim', 'sim_bringup.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'enable_exploration_demo': 'false',
            'enable_rviz': enable_rviz,
            'enable_gui': enable_gui,
            'world_file': world_file,
            'real_time_factor': LaunchConfiguration('real_time_factor'),
            'x_pose': LaunchConfiguration('x_pose'),
            'y_pose': LaunchConfiguration('y_pose'),
            'z_pose': LaunchConfiguration('z_pose'),
            'yaw': LaunchConfiguration('yaw'),
            'rviz_config_file': os.path.join(
                get_package_share_directory('gemstone_frontier_explorer'),
                'rviz', 'auto_mapping.rviz'),
        }.items(),
    )

    lidar_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_launch_path('gemstone_lidar_bringup', 'lidar_bringup.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'enable_rplidar': 'false',          # sim'de /scan Gazebo'dan
            'enable_rf2o': 'false',             # sim'de /odom Gazebo'dan
            'enable_obstacle_avoidance': 'false',  # sim_bringup sagliyor
            'enable_naive_avoidance': 'false',
            'enable_slam_toolbox': 'true',
            'enable_nav2': 'true',
            'nav2_params_file': nav2_params,
            'nav2_cmd_vel_topic': 'cmd_vel_nav',
            'odom_topic': '/odom',
        }.items(),
    )

    explorer_node = Node(
        package='gemstone_frontier_explorer',
        executable='frontier_explorer_node',
        name='frontier_explorer_node',
        output='screen',
        parameters=[explorer_params, {'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_enable_rviz,
        declare_enable_gui,
        declare_real_time_factor,
        declare_world_file,
        declare_x_pose,
        declare_y_pose,
        declare_z_pose,
        declare_yaw,
        sim_bringup,
        lidar_bringup,
        explorer_node,
    ])
