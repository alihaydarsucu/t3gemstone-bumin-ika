# Revizyon Geçmişi

## 2026-07-28
- ilk taslak repo oluşturuldu
- Linux-first mimari netleştirildi
- kamera sürücüsü ve örnek işleme node'u için alan açıldı
- ROS 2 paket iskeleti eklenmeye başlandı
- mimari kararlar netleşti: diferansiyel sürüş (2 tahrik teker + ön misket
  teker), motor kontrolü UART üzerinden harici sürücü karta (GPIO değil),
  RPLidar A1M8 için Slamtec'in resmi `sllidar_ros2` paketi
- 7 ROS 2 paketi eklendi: `gemstone_imu` (ICM-20948 SPI, T3 Foundation C
  kütüphanesi), `gemstone_motor_driver` (UART, birim testli kinematik),
  `gemstone_camera` + `gemstone_image_proc` (CSI/v4l2_camera), 
  `gemstone_lidar_bringup` (sllidar_ros2 + rf2o + slam_toolbox + Nav2),
  `gemstone_obstacle_avoidance` (birim testli fail-safe karar node'u),
  `gemstone_bringup` (URDF + master launch)
- eski tek-paket IMU taslağı (`imu_node.py`, spidev tabanlı) kaldırıldı;
  yerine T3 Foundation'ın resmi C sürücü kütüphanesini kullanan
  `gemstone_imu` (C++) getirildi
- README, BLUEPRINT ve tüm `docs/tr/*` sayfaları gerçek implementasyonu
  yansıtacak şekilde güncellendi

## 2026-07-30
- mimari karar değişti: motor kontrolü artık UART ile harici sürücü kart
  yerine, Gemstone'un GPIO'larından (libgpiod) **doğrudan** Harezmi
  robotunun motor+enkoder kartını (MX1508 H-bridge) sürüyor -- kart
  üzerindeki Deneyap sökülüp yerine Gemstone geçti; güç harici 2S pilden,
  lojik Gemstone'un 3.3V+GND'sinden besleniyor
- `gemstone_motor_driver` yeniden yazıldı: UART/`protocol.py` kaldırıldı,
  yerine `gpio_motor.py` (H-bridge yön kontrolü) ve `quadrature_encoder.py`
  (kadratür enkoder tik sayımı) eklendi; `differential_drive.py`'ye ters
  kinematik (`wheel_speeds_to_twist`) ve odometri entegrasyonu
  (`OdometryIntegrator`) eklendi, `/wheel_odom` yayınlanıyor
- yeni paket: `gemstone_ultrasonic` (HC-SR04 benzeri sensör, GPIO/libgpiod,
  `sensor_msgs/Range` yayınlıyor)
- `gemstone_bringup/launch/bringup.launch.py`'ye `enable_ultrasonic`
  argümanı eklendi
- Harezmi-Deneyap resmi pin haritası PDF'i incelendi, multimetre
  ölçümleriyle doğrulandı; tam eşleme `hardware/README.md`'de
