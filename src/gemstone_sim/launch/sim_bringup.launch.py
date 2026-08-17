"""gemstone_sim: Gazebo Classic + gemstone uygulama node'larini birlikte
ayaga kaldiran simülasyon launch dosyasi.

Gercek donanim katmanlarinin (motor surucu, imu surucu, lidar sürücü, kamera
sürücü) yerini gazebo_ros plugin'leri alir:

  - libgazebo_ros_diff_drive  -> /cmd_vel dinler, /odom + odom->base_link TF
  - libgazebo_ros_ray_sensor  -> /scan
  - libgazebo_ros_imu_sensor  -> /imu/data
  - libgazebo_ros_camera      -> /camera/image_raw
  - libgazebo_ros_joint_state -> /joint_states

Ust katman (gemstone) node'lari oldugu gibi calisir:
  motion_state_node         : /imu/data + /odom -> /motion_state/odom
  exploration_demo_node     : /scan + /motion_state/odom -> /cmd_vel_nav
  obstacle_avoidance_node   : /scan + /cmd_vel_nav -> /cmd_vel (güvenlik filtresi)
  image_processing_node     : /camera/image_raw -> /camera/image_processed

Ornek kullanim:
  ros2 launch gemstone_sim sim_bringup.launch.py
  ros2 launch gemstone_sim sim_bringup.launch.py enable_rviz:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    sim_share = get_package_share_directory('gemstone_sim')
    exploration_demo_share = get_package_share_directory('gemstone_exploration_demo')

    world_file = LaunchConfiguration('world_file')
    xacro_file = os.path.join(sim_share, 'urdf', 'gemstone_ugv_gazebo.xacro')
    motion_state_params = os.path.join(sim_share, 'config', 'motion_state_sim_params.yaml')
    exploration_params = os.path.join(
        exploration_demo_share, 'params', 'exploration_demo_params.yaml')

    # Xacro'yu URDF'e cevir (xacro paketi Python olarak kullanilir).
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # --- Argumanlar ---
    use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='true')
    enable_gui = DeclareLaunchArgument('enable_gui', default_value='true')
    enable_rviz = DeclareLaunchArgument('enable_rviz', default_value='false')
    enable_exploration_demo = DeclareLaunchArgument(
        'enable_exploration_demo', default_value='true',
        description='Eski reaktif exploration_demo_node\'i calistirir. '
                    'Otonom kesif (auto_mapping) modunda false verilir, '
                    'cunku frontier_explorer_node da cmd_vel_nav\'a yazar.')
    x_pose = DeclareLaunchArgument('x_pose', default_value='0.0')
    y_pose = DeclareLaunchArgument('y_pose', default_value='0.0')
    z_pose = DeclareLaunchArgument('z_pose', default_value='0.075')
    yaw = DeclareLaunchArgument('yaw', default_value='0.0')
    world_file_arg = DeclareLaunchArgument(
        'world_file',
        default_value=PathJoinSubstitution([sim_share, 'worlds', 'office.world']),
        description='Gazebo dünya dosyasi (mutlak yol). Varsayilan: office.world.')
    rviz_config_file_arg = DeclareLaunchArgument(
        'rviz_config_file',
        default_value=os.path.join(
            get_package_share_directory('gemstone_frontier_explorer'),
            'rviz', 'auto_mapping.rviz'),
        description='RViz config dosyasinin mutlak yolu.')

    # --- Gazebo ---
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    gzserver = ExecuteProcess(
        cmd=[
            'gzserver', world_file, '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
        ],
        output='screen',
    )

    gzclient = ExecuteProcess(
        cmd=['gzclient'],
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_gui')),
    )

    # gzserver'in dünyayı yüklemesine zaman tanıyıp sonra gzclient'i aç.
    start_gzclient = TimerAction(period=5.0, actions=[gzclient])

    # --- Robot ---
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'robot_description': robot_description,
        }],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_gemstone_ugv',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'gemstone_ugv',
            '-x', LaunchConfiguration('x_pose'),
            '-y', LaunchConfiguration('y_pose'),
            '-z', LaunchConfiguration('z_pose'),
            '-Y', LaunchConfiguration('yaw'),
        ],
    )

    # --- Ust katman gemstone node'lari ---
    motion_state_node = Node(
        package='gemstone_motor_driver',
        executable='motion_state_node',
        name='motion_state_node',
        output='screen',
        parameters=[motion_state_params, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
    )

    exploration_demo_node = Node(
        package='gemstone_exploration_demo',
        executable='gemstone_exploration_demo_node',
        name='gemstone_exploration_demo_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_exploration_demo')),
        parameters=[exploration_params, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
    )

    obstacle_avoidance_node = Node(
        package='gemstone_obstacle_avoidance',
        executable='obstacle_avoidance_node',
        name='obstacle_avoidance_node',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            # Kapali/dar ortam (ev) icin cok konservatif olmasin: ofis icin 0.4,
            # ev kapilari (~0.9 m) icin 0.25 m guvenlik yeterli.
            'safety_distance': 0.30,
        }],
    )

    image_processing_node = Node(
        package='gemstone_image_proc',
        executable='image_processing_node',
        name='image_processing_node',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_rviz')),
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        arguments=['-d', LaunchConfiguration('rviz_config_file')],
    )

    return LaunchDescription([
        use_sim_time,
        enable_gui,
        enable_rviz,
        enable_exploration_demo,
        x_pose,
        y_pose,
        z_pose,
        yaw,
        world_file_arg,
        rviz_config_file_arg,
        gzserver,
        start_gzclient,
        robot_state_publisher,
        spawn_entity,
        motion_state_node,
        exploration_demo_node,
        obstacle_avoidance_node,
        image_processing_node,
        rviz_node,
    ])
