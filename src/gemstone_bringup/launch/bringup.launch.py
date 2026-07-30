"""Aracin TUM surucu node'larini tek yerden ayaga kaldiran master launch
dosyasi. Her katman ayri bir launch argumaniyla acilip kapatilabilir --
NOT: karta baglanip her node'u tek tek test etmeden hepsini birden
acmayin, bu launch dosyasi "hepsi calisir hale gelince birlestirme" adimi
icin hazirlandi.

Ornek kullanim:
  # Sadece IMU + motor surucu (ilk saha testi):
  ros2 launch gemstone_bringup bringup.launch.py \\
      enable_camera:=false enable_lidar_stack:=false

  # Hepsi + haritalama modu:
  ros2 launch gemstone_bringup bringup.launch.py \\
      enable_slam_toolbox:=true
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    bringup_share = get_package_share_directory('gemstone_bringup')
    lidar_bringup_share = get_package_share_directory('gemstone_lidar_bringup')
    camera_share = get_package_share_directory('gemstone_camera')

    xacro_file = os.path.join(bringup_share, 'urdf', 'gemstone_ugv.urdf.xacro')
    imu_params_file = os.path.join(bringup_share, 'params', 'imu_params.yaml')
    motor_params_file = os.path.join(bringup_share, 'params', 'motor_driver_params.yaml')
    ultrasonic_params_file = os.path.join(bringup_share, 'params', 'ultrasonic_params.yaml')

    # --- Ust duzey ac/kapat argumanlari ---
    enable_imu = DeclareLaunchArgument('enable_imu', default_value='true')
    enable_imu_filter = DeclareLaunchArgument('enable_imu_filter', default_value='true')
    enable_motor_driver = DeclareLaunchArgument('enable_motor_driver', default_value='true')
    enable_ultrasonic = DeclareLaunchArgument('enable_ultrasonic', default_value='false')
    enable_camera = DeclareLaunchArgument('enable_camera', default_value='true')
    enable_image_proc = DeclareLaunchArgument('enable_image_proc', default_value='true')
    enable_lidar_stack = DeclareLaunchArgument('enable_lidar_stack', default_value='true')
    enable_state_publishers = DeclareLaunchArgument('enable_state_publishers', default_value='true')
    enable_rviz = DeclareLaunchArgument('enable_rviz', default_value='false')

    # gemstone_lidar_bringup'a gecirilecek alt argumanlar (varsayilanlari orada)
    enable_slam_toolbox = DeclareLaunchArgument('enable_slam_toolbox', default_value='false')
    enable_nav2 = DeclareLaunchArgument('enable_nav2', default_value='false')

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_state_publishers')),
        parameters=[{
            'robot_description': ParameterValue(Command(['xacro ', xacro_file]), value_type=str),
        }],
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_state_publishers')),
    )

    imu_node = Node(
        package='gemstone_imu',
        executable='icm20948_driver_node',
        name='icm20948_driver_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_imu')),
        parameters=[imu_params_file],
    )

    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_madgwick_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_imu_filter')),
        parameters=[imu_params_file],
        # imu_filter_madgwick varsayilan olarak imu/data_raw'i dinler ve
        # imu/data'yi yayinlar; icm20948_driver_node ile ayni isimler
        # oldugu icin ek remap gerekmiyor.
    )

    motor_driver_node = Node(
        package='gemstone_motor_driver',
        executable='motor_driver_node',
        name='motor_driver_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_motor_driver')),
        parameters=[motor_params_file],
    )

    ultrasonic_node = Node(
        package='gemstone_ultrasonic',
        executable='ultrasonic_node',
        name='ultrasonic_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_ultrasonic')),
        parameters=[ultrasonic_params_file],
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([camera_share, 'launch', 'camera.launch.py'])
        ),
        condition=IfCondition(LaunchConfiguration('enable_camera')),
    )

    image_proc_node = Node(
        package='gemstone_image_proc',
        executable='image_processing_node',
        name='image_processing_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_image_proc')),
    )

    lidar_stack_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([lidar_bringup_share, 'launch', 'lidar_bringup.launch.py'])
        ),
        condition=IfCondition(LaunchConfiguration('enable_lidar_stack')),
        launch_arguments={
            'enable_slam_toolbox': LaunchConfiguration('enable_slam_toolbox'),
            'enable_nav2': LaunchConfiguration('enable_nav2'),
        }.items(),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_rviz')),
    )

    return LaunchDescription([
        enable_imu,
        enable_imu_filter,
        enable_motor_driver,
        enable_ultrasonic,
        enable_camera,
        enable_image_proc,
        enable_lidar_stack,
        enable_state_publishers,
        enable_rviz,
        enable_slam_toolbox,
        enable_nav2,
        robot_state_publisher_node,
        joint_state_publisher_node,
        imu_node,
        imu_filter_node,
        motor_driver_node,
        ultrasonic_node,
        camera_launch,
        image_proc_node,
        lidar_stack_launch,
        rviz_node,
    ])
