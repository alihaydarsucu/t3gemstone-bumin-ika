# Mimari

## Genel Akış

```
IMU (SPI) / A1M8 Lidar (USB) / CSI Kamera / Motor Sürücü Kart (UART)
        │
        ▼
A53 / Linux Katmanı (T3 Gemstone O1, tek kart)
        ├── gemstone_imu             -> imu/data_raw
        ├── gemstone_motor_driver    -> UART (cmd_vel'i dinler)
        ├── gemstone_camera          -> camera/image_raw
        ├── gemstone_image_proc      -> camera/image_processed
        ├── gemstone_lidar_bringup   -> scan, odom_rf2o, map
        ├── gemstone_obstacle_avoidance -> guvenlik/karar katmani
        └── gemstone_bringup         -> hepsini birlestiren master launch
```

## Katmanlar

### Linux / A53
- board init (SPI/UART/CSI/USB cihaz erisimi)
- driver init (her paket kendi donanimini acar)
- topic publish (standart ROS mesaj tipleriyle)
- watchdog (motor surucude cmd_vel timeout, obstacle avoidance'ta lidar stale-check)
- motor safety (fail-safe: veri gelmezse dur)
- kamera isleme ornegi (iskelet, gercek CV gorevi eklenecek)
- logging / visualization (diagnostic_updater + RViz)

## Mimari Kural

Bu projede sensör verisi ve ROS topic'leri tamamen Linux tarafında üretilir.
Ayrı bir mikrodenetleyici (Deneyap vb.) veya RTOS/R5F katmanı **kullanılmıyor**;
motor sürücüsü bile Linux'tan UART üzerinden harici bir sürücü karta komut
göndererek çalışıyor.

## Tasarım Sonucu

Bu yaklaşım sayesinde:

- açılış daha sade olur
- kontrol akışı tek yerde (tek kart, tek Linux) toplanır
- sensör ve motor akışı tek launch altında yönetilir
- kamera gibi ağır işler ayrı node'lara bölünebilir
- her katman (`enable_imu`, `enable_motor_driver`, `enable_camera`,
  `enable_lidar_stack`, `enable_slam_toolbox`, `enable_nav2`) bağımsız
  açılıp kapanabildiği için saha testi kademeli yapılabilir
