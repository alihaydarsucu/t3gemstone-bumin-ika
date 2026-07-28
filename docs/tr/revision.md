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
