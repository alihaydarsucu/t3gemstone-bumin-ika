# Bringup

## Bringup Nedir?

Bringup, kartın açılışta robotik çalışma için hazır hale getirilmesidir.
Bu proje için bringup şu adımları kapsar:

1. board init
2. driver init
3. ROS 2 node start
4. topic publish
5. health check

## Başlangıç Akışı

- güç verilir
- Linux ayağa kalkar
- `ros2 launch gemstone_bringup bringup.launch.py` çalıştırılır
- `gemstone_imu` (ICM-20948, SPI) başlatılır -> `imu/data_raw`
- `gemstone_motor_driver` başlatılır, `cmd_vel`'i dinlemeye başlar
- `gemstone_camera` (v4l2_camera, CSI) başlatılır -> `camera/image_raw`
- `gemstone_image_proc` başlatılır -> `camera/image_processed`
- `gemstone_lidar_bringup` başlatılır: `sllidar_ros2` -> `scan`,
  `rf2o_laser_odometry` -> `odom_rf2o`, `gemstone_obstacle_avoidance` devrede
- istenirse `enable_slam_toolbox:=true` ile haritalama, `enable_nav2:=true`
  ile otonom navigasyon eklenir

## Önerilen Sıra

Hepsini birden açmadan önce her katmanı tek tek doğrulamak için
`gemstone_ws/README.md` içindeki "Önerilen test sırası" bölümüne bakın:
önce IMU, sonra motor sürücü (teker havada/blok üzerinde), sonra kamera,
sonra lidar, sonra engelden kaçınma, sonra haritalama, en son Nav2.

## Hedef Çıktı

Bu bölüm sonunda tek kart, `ros2 launch gemstone_bringup bringup.launch.py`
ile robot kontrolü için kullanılabilir bir durumda olur.
