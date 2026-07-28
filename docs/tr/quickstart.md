# Hızlı Başlangıç

Bu sayfa, Gemstone bringup hattını gerçekten çalıştırmak için gereken adımları toplar.

## Ne Çalışıyor?

Şu anki launch akışı iki gerçek parçayı hedefler:

1. `ICM-20948` IMU node'u
2. A1M8 için Slamtec ROS 2 lidar launch'u

## Ön Koşullar

### Sistem

- Linux üzerinde ROS 2 Humble kurulu olmalı
- `/dev/spidev0.3` erişimi olmalı
- `/dev/ttyUSB0` erişimi olmalı

### Paketler

- `python3-spidev`
- `sllidar_ros2`
- `sensor_msgs`

## Tavsiye Edilen Kurulum

Bu repo, host sistemde ROS 2 kurulumu varsa doğrudan çalışabilir.
Kurulum yoksa kökteki `Dockerfile` ile izole test yapmak daha güvenlidir.

### Seçenek 1: Host Üzerinde

1. ROS 2 ortamını yükle:

```bash
source /opt/ros/humble/setup.bash
```

2. Workspace kökünde build et:

```bash
colcon build --symlink-install
```

3. Ortamı source et:

```bash
source install/setup.bash
```

4. Launch'u çalıştır:

```bash
ros2 launch gemstone_bringup bringup.launch.py
```

### Seçenek 2: Docker ile

1. İmaj oluştur:

```bash
docker build -t gemstone-bringup-humble .
```

2. Container başlat:

```bash
docker run -it --rm --device=/dev/spidev0.3 --device=/dev/ttyUSB0 -v "$PWD:/workspace" gemstone-bringup-humble
```

3. Container içinde ROS ortamını yükle:

```bash
source /opt/ros/humble/setup.bash
```

4. Build et:

```bash
colcon build --symlink-install
```

5. Çalıştır:

```bash
source install/setup.bash
ros2 launch gemstone_bringup bringup.launch.py
```

## Launch Ne Başlatır?

`bringup.launch.py` şu iki şeyi başlatır:

1. `gemstone_imu`
   - ICM-20948 IMU sensörünü SPI üzerinden açar
   - `/gemstone/imu/data` topic'ine `sensor_msgs/Imu` yayınlar

2. `sllidar_ros2`
   - A1M8 lidar için Slamtec ROS 2 launch'unu açar
   - varsayılan olarak `/dev/ttyUSB0` ve `115200` baudrate kullanır

## Launch Parametreleri

İstersen varsayılanları override edebilirsin:

```bash
ros2 launch gemstone_bringup bringup.launch.py \
  imu_spi_device:=/dev/spidev0.3 \
  imu_frame_id:=icm20948_link \
  imu_publish_rate_hz:=100.0 \
  lidar_serial_port:=/dev/ttyUSB0 \
  lidar_serial_baudrate:=115200
```

## Beklenen Topic'ler

- `/gemstone/imu/data`
- `/scan`

## Sorun Çıkarırsa

- `python3-spidev` yoksa IMU node açılmaz
- `sllidar_ros2` yoksa lidar launch açılmaz
- cihaz izinleri yoksa `spidev` ve `ttyUSB0` erişimi başarısız olur
- yanlış baudrate veya yanlış port, lidar scan başlatmayı engeller

## Kontrol İçin Hızlı Komutlar

```bash
ros2 topic list
ros2 topic echo /gemstone/imu/data
ros2 topic echo /scan
```
