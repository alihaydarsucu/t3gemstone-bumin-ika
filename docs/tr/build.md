# Kurulum ve Build

Bu repo Linux-first bir ROS 2 çalışma alanı olarak hazırlanır.

## Beklenen Yerleşim

- `src/gemstone_bringup/` - ROS 2 paket kodu
- `docs/` - proje notları
- `hardware/` - bağlantı bilgileri
- `tools/` - yardımcı betikler

## Build Mantığı

ROS 2 kurulu bir sistemde tipik akış:

1. workspace kökünde `colcon build`
2. ortamı `source install/setup.bash` ile yükleme
3. `ros2 launch gemstone_bringup bringup.launch.py` ile çalıştırma

## Gerekli Bağımlılıklar

- ROS 2 Humble
- Slamtec ROS 2 lidar paketi `sllidar_ros2` (apt'ta yoksa kaynak koddan clone)
- `rf2o_laser_odometry` (apt'ta yoksa kaynak koddan clone)
- `ros-humble-v4l2-camera`, `ros-humble-cv-bridge` (kamera)
- `ros-humble-slam-toolbox`, `ros-humble-navigation2`, `ros-humble-nav2-bringup`
- `ros-humble-imu-filter-madgwick`
- `ros-humble-robot-state-publisher`, `ros-humble-joint-state-publisher`, `ros-humble-xacro`
- `ros-humble-diagnostic-updater`
- `python3-libgpiod` (motor + enkoder + ultrasonik GPIO), `python3-opencv`
- `/dev/spidev0.3` erişimi (dahili IMU)
- GPIO erişimi (`gpiodetect`/`gpioinfo` ile chip adı ve line offsetlerini
  bulun) — motor, enkoder, ultrasonik
- `/dev/ttyUSB0` erişimi (RPLidar)

Varsayılan A1M8 baudrate değeri `115200` olarak ayarlanır.

## Container Yolu

Bu repo içinde bir `Dockerfile` bulunur.
Bu yol, ROS 2 Humble kurulumu olmayan ya da yerel binary paketleri için uygun olmayan sistemlerde daha güvenli bir test ortamı sağlar. Dockerfile, apt'ta olmayan
`rf2o_laser_odometry` ve `sllidar_ros2`'yi build sırasında otomatik clone'lar.

Not: gerçek donanım erişimi (SPI/GPIO/CSI) sadece kartın kendisinde mümkündür;
container yalnızca derleme/kod testinde yardımcı olur, donanımsız node'ları
(kinematik, protokol, lidar karar mantığı gibi) test etmek için de kullanılabilir.

Önerilen akış:

1. `docker build -t gemstone-bringup-humble .`
2. `docker run -it --rm -v "$PWD:/workspace" gemstone-bringup-humble`
3. container içinde `source /opt/ros/humble/setup.bash`
4. ardından `colcon build`

## Not

Bu proje için hedef, tüm ana iş akışını Linux üzerinde çalıştırmaktır.
