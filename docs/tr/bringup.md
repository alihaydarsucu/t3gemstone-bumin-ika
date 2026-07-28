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
- systemd veya benzeri servis yöneticisi bringup servisini başlatır
- ROS 2 launch çalışır
- ICM-20948 IMU node'u başlatılır
- A1M8 için Slamtec ROS 2 lidar launch'u başlatılır
- IMU verisi `/gemstone/imu/data` topic'ine akar
- lidar verisi `/scan` ve ilgili topic'lere akar

## Hedef Çıktı

Bu bölüm sonunda tek kart, robot kontrolü için kullanılabilir bir durumda olur.
