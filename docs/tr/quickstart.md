# Hızlı Başlangıç

Bu sayfa, Gemstone bringup hattını gerçekten çalıştırmak için gereken adımları toplar.

## Ne Çalışıyor?

Şu anki launch akışı (`gemstone_bringup/launch/bringup.launch.py`) şu parçaları
kapsar, hepsi ayrı bir `enable_*` argümanıyla açılıp kapanabilir:

1. `gemstone_imu` — ICM-20948 IMU node'u (`enable_imu`)
2. `imu_filter_madgwick` — ham IMU'ya yönelim ekler (`enable_imu_filter`)
3. `gemstone_motor_driver` — GPIO (libgpiod) motor sürücü + enkoder odometrisi (`enable_motor_driver`)
4. `gemstone_ultrasonic` — GPIO (libgpiod) ultrasonik mesafe sensörü (`enable_ultrasonic`, varsayılan kapalı)
5. `gemstone_camera` — CSI kamera (`enable_camera`)
6. `gemstone_image_proc` — görüntü işleme iskeleti (`enable_image_proc`)
7. `gemstone_lidar_bringup` — A1M8 lidar + rf2o + engelden kaçınma
   (`enable_lidar_stack`, kendi içinde `enable_slam_toolbox`/`enable_nav2`)

## Ön Koşullar

### Sistem

- Linux üzerinde ROS 2 Humble kurulu olmalı
- `/dev/spidev0.3` erişimi olmalı (dahili IMU)
- GPIO erişimi olmalı (motor + enkoder + ultrasonik) — karta bağlanınca
  `gpiodetect` ve `gpioinfo` ile gerçek chip adı/line offsetlerini bulup
  `gemstone_bringup/params/motor_driver_params.yaml` ve
  `ultrasonic_params.yaml` içine yazın
- `/dev/ttyUSB0` erişimi olmalı (RPLidar A1M8)

### Paketler

Tam liste için [build.md](build.md); özetle: `ros-humble-v4l2-camera`,
`ros-humble-cv-bridge`, `ros-humble-slam-toolbox`,
`ros-humble-navigation2`/`nav2-bringup`, `ros-humble-imu-filter-madgwick`,
`ros-humble-robot-state-publisher`, `ros-humble-joint-state-publisher`,
`ros-humble-xacro`, `ros-humble-diagnostic-updater`, `python3-libgpiod`,
`python3-opencv`, ve kaynaktan clone edilecek `rf2o_laser_odometry` +
`sllidar_ros2`.

## Tavsiye Edilen Kurulum

### Seçenek 1: Host Üzerinde (kartın kendisi)

```bash
source /opt/ros/humble/setup.bash
cd src   # bu repo + rf2o_laser_odometry + sllidar_ros2 burada olmali
rosdep install --from-paths . --ignore-src -r -y
cd ..
colcon build --symlink-install
source install/setup.bash
ros2 launch gemstone_bringup bringup.launch.py
```

### Seçenek 2: Docker ile (donanımsız kod/derleme testi)

```bash
docker build -t gemstone-bringup-humble .
docker run -it --rm --device=/dev/spidev0.3 --device=/dev/gpiochip0 --device=/dev/ttyUSB0 \
  -v "$PWD:/workspace" gemstone-bringup-humble
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch gemstone_bringup bringup.launch.py
```

## Kademeli Test (önerilir)

Hepsini birden açmadan önce her katmanı tek tek doğrulayın. Özet:

```bash
# 1) sadece IMU
ros2 launch gemstone_bringup bringup.launch.py \
  enable_motor_driver:=false enable_camera:=false enable_image_proc:=false enable_lidar_stack:=false

# 2) IMU + motor (teker havada/blok uzerinde!)
ros2 launch gemstone_bringup bringup.launch.py \
  enable_camera:=false enable_image_proc:=false enable_lidar_stack:=false

# 3) + ultrasonik (kablolandiysa)
ros2 launch gemstone_bringup bringup.launch.py \
  enable_ultrasonic:=true enable_camera:=false enable_image_proc:=false enable_lidar_stack:=false

# 4) hepsi, haritalama modu
ros2 launch gemstone_bringup bringup.launch.py enable_slam_toolbox:=true
```

## Beklenen Topic'ler

```bash
ros2 topic list
ros2 topic echo /imu/data_raw
ros2 topic echo /scan
ros2 topic echo /camera/image_raw
ros2 topic echo /wheel_odom
```

## Sorun Çıkarırsa

- IMU açılmıyorsa `/dev/spidev0.3` izinlerini kontrol edin
- motor sürücü/ultrasonik açılmıyorsa GPIO chip adı/line offsetlerini
  kontrol edin (bkz. [troubleshooting.md](troubleshooting.md))
- lidar açılmıyorsa `sllidar_ros2` kurulu mu, `/dev/ttyUSB0` doğru mu kontrol edin
- kamera açılmıyorsa CSI overlay + `gem-camera-setup` adımlarını tekrarlayın
