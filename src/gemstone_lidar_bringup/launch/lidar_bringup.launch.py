"""RPLIDAR A1M8 + rf2o_laser_odometry + slam_toolbox + Nav2'yi tek launch
dosyasinda toplar. Her katman ayri bir launch argumaniyla acilip kapatilir,
boylece hepsini birden calistirmadan once tek tek dogrulayabilirsiniz:

  1) enable_slam_toolbox:=false enable_nav2:=false ile sadece rplidar+rf2o'yu
     acip RViz'de /scan ve /odom_rf2o'nun dogru geldigini kontrol edin.
  2) enable_slam_toolbox:=true ile haritalama yapip calistigini görün.
  3) En son enable_nav2:=true ile tam otonom navigasyonu deneyin (Nav2
     parametreleri icin params/nav2_overrides.md dosyasina bakin).

Bu paket sllidar_ros2 (Slamtec'in resmi A1M8 ROS 2 paketi),
rf2o_laser_odometry, slam_toolbox ve nav2_bringup'a bagimlidir; bunlar ekip
tarafindan yazilmadigi icin kaynak kodlari bu repoya eklenmez (third-party,
ayrica clone/apt install edilmesi gerekir).
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('gemstone_lidar_bringup')
    exploration_demo_share = get_package_share_directory('gemstone_exploration_demo')
    naive_avoidance_params_file = os.path.join(
        exploration_demo_share, 'params', 'naive_avoidance_params.yaml')

    enable_rplidar = DeclareLaunchArgument('enable_rplidar', default_value='true')
    enable_rf2o = DeclareLaunchArgument('enable_rf2o', default_value='true')
    enable_obstacle_avoidance = DeclareLaunchArgument('enable_obstacle_avoidance', default_value='true')
    # Projenin asil otonom hareket davranisi gemstone_exploration_demo'daki
    # durum makineli algoritma; bu, enansakib/obstacle-avoidance-turtlebot'tan
    # portlanmis basit/ogretici bir alternatif -- varsayilan KAPALI. İkisini
    # ayni anda acmayin, ikisi de cmd_vel_nav'a yazar, komutlar birbirine
    # karisir.
    enable_naive_avoidance = DeclareLaunchArgument('enable_naive_avoidance', default_value='false')
    enable_slam_toolbox = DeclareLaunchArgument('enable_slam_toolbox', default_value='false')
    enable_nav2 = DeclareLaunchArgument('enable_nav2', default_value='false')
    # Gercek donanimda use_sim_time:=false; Gazebo simülasyonunda true.
    use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='false')

    serial_port = DeclareLaunchArgument('lidar_serial_port', default_value='/dev/ttyUSB0')
    frame_id = DeclareLaunchArgument('lidar_frame_id', default_value='lidar_link')

    nav2_params_file = DeclareLaunchArgument(
        'nav2_params_file',
        default_value=os.path.join(pkg_share, 'params', 'nav2_params.yaml'),
        description='Nav2 params yolu (bkz. params/nav2_overrides.md)')
    nav2_cmd_vel_topic = DeclareLaunchArgument(
        'nav2_cmd_vel_topic', default_value='cmd_vel_nav',
        description="Nav2 hiz cikti topic'i (guvenlik katmaninin giris topic'i)")

    rplidar_launch = GroupAction(
        condition=IfCondition(LaunchConfiguration('enable_rplidar')),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        get_package_share_directory('sllidar_ros2'),
                        'launch', 'sllidar_a1_launch.py',
                    ])
                ),
                launch_arguments={
                    'channel_type': 'serial',
                    'serial_port': LaunchConfiguration('lidar_serial_port'),
                    'serial_baudrate': '115200',
                    'frame_id': LaunchConfiguration('lidar_frame_id'),
                }.items(),
            )
        ],
    )

    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_rf2o')),
        parameters=[{
            'laser_scan_topic': '/scan',
            'odom_topic': '/odom_rf2o',
            'publish_tf': True,
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'freq': 20.0,
            'init_pose_from_topic': '',
        }],
    )

    obstacle_avoidance_node = Node(
        package='gemstone_obstacle_avoidance',
        executable='obstacle_avoidance_node',
        name='obstacle_avoidance_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_obstacle_avoidance')),
        parameters=[{
            'scan_topic': 'scan',
            'input_cmd_vel_topic': 'cmd_vel_nav',
            'output_cmd_vel_topic': 'cmd_vel',
            'safety_distance': 0.4,
            'forward_half_angle_deg': 30.0,
        }],
    )

    naive_avoidance_node = Node(
        package='gemstone_exploration_demo',
        executable='naive_avoidance_node',
        name='naive_avoidance_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_naive_avoidance')),
        parameters=[naive_avoidance_params_file],
    )

    slam_toolbox_launch = GroupAction(
        condition=IfCondition(LaunchConfiguration('enable_slam_toolbox')),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        get_package_share_directory('slam_toolbox'),
                        'launch', 'online_async_launch.py',
                    ])
                ),
                launch_arguments={
                    'slam_params_file': os.path.join(pkg_share, 'params', 'slam_toolbox_mapping.yaml'),
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                }.items(),
            )
        ],
    )

    nav2_launch = GroupAction(
        condition=IfCondition(LaunchConfiguration('enable_nav2')),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        pkg_share,
                        'launch', 'nav2_launch.py',
                    ])
                ),
                launch_arguments={
                    'params_file': LaunchConfiguration('nav2_params_file'),
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                    'cmd_vel_topic': LaunchConfiguration('nav2_cmd_vel_topic'),
                }.items(),
            )
        ],
    )

    return LaunchDescription([
        enable_rplidar,
        enable_rf2o,
        enable_obstacle_avoidance,
        enable_naive_avoidance,
        enable_slam_toolbox,
        enable_nav2,
        use_sim_time,
        serial_port,
        frame_id,
        nav2_params_file,
        nav2_cmd_vel_topic,
        rplidar_launch,
        rf2o_node,
        obstacle_avoidance_node,
        naive_avoidance_node,
        slam_toolbox_launch,
        nav2_launch,
    ])
