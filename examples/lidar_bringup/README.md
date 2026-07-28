# Lidar Bringup Örneği

Bu örneğin gerçek implementasyonu artık `src/gemstone_lidar_bringup`
paketinde yaşıyor (`launch/lidar_bringup.launch.py`).

## Ne Yapıyor (bugün)

- Slamtec'in resmi `sllidar_ros2` paketiyle A1M8'i USB üzerinden açar (`scan`)
- `rf2o_laser_odometry` ile lazer tabanlı odometri üretir (`odom_rf2o`)
- `gemstone_obstacle_avoidance` ile gerçek zamanlı engelden kaçınma sağlar
- isteğe bağlı olarak `slam_toolbox` (haritalama) ve Nav2 (otonom navigasyon)
  ekler — her biri ayrı bir launch argümanıyla (`enable_slam_toolbox`,
  `enable_nav2`) açılıp kapanır

## Sonraki Adım

Kart üzerinde tek tek doğrulama için
[../../docs/tr/quickstart.md](../../docs/tr/quickstart.md) ve
[../../gemstone_ws/README.md](../../gemstone_ws/README.md) içindeki
"Önerilen test sırası" bölümüne bakın.
