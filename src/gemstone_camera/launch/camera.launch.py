"""T3 Gemstone O1 CSI kamerasini (IMX219/OV5640) v4l2_camera_node ile ROS 2'ye
baglayan launch dosyasi.

On kosul: karti kurarken docs.t3gemstone.org/tr/boards/o1/peripherals/camera.md
adimlarini takip edip (device tree overlay + `gem-camera-setup`) /dev/videoX
node'unun goruntuye hazir oldugundan emin olun. Surucu kodu burada yazilmaz;
ros-humble-v4l2-camera paketine bagimlidir (third-party, apt ile kurulur).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    video_device_arg = DeclareLaunchArgument(
        'video_device', default_value='/dev/video0',
        description='CSI kameranin v4l2 device path (gem-camera-setup sonrasi olusan /dev/videoX)')
    image_width_arg = DeclareLaunchArgument('image_width', default_value='1280')
    image_height_arg = DeclareLaunchArgument('image_height', default_value='720')
    frame_id_arg = DeclareLaunchArgument(
        'frame_id', default_value='camera_link',
        description='Goruntu mesajlarinda kullanilacak TF frame id')
    camera_info_url_arg = DeclareLaunchArgument(
        'camera_info_url', default_value='',
        description='Kalibrasyon dosyasi varsa file:///... URL, yoksa bos birakin')

    v4l2_camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='gemstone_camera',
        output='screen',
        parameters=[{
            'video_device': LaunchConfiguration('video_device'),
            'image_size': [LaunchConfiguration('image_width'), LaunchConfiguration('image_height')],
            'camera_frame_id': LaunchConfiguration('frame_id'),
            'camera_info_url': LaunchConfiguration('camera_info_url'),
        }],
        remappings=[
            ('image_raw', 'camera/image_raw'),
            ('camera_info', 'camera/camera_info'),
        ],
    )

    return LaunchDescription([
        video_device_arg,
        image_width_arg,
        image_height_arg,
        frame_id_arg,
        camera_info_url_arg,
        v4l2_camera_node,
    ])
