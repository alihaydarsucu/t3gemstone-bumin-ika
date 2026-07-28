# Mesaj Tanımları

## Karar: Özel `.msg` yok

Bu proje özel bir mesaj tipi tanımlamıyor. Bunun yerine standart ROS 2 mesaj
tipleri kullanılıyor, böylece teleop/rqt/Nav2/slam_toolbox gibi hazır araçlar
ek dönüşüm olmadan doğrudan çalışıyor:

| Veri | Mesaj Tipi | Topic |
|---|---|---|
| IMU (ham) | `sensor_msgs/Imu` | `imu/data_raw` |
| IMU (yönelimli) | `sensor_msgs/Imu` | `imu/data` |
| Lidar tarama | `sensor_msgs/LaserScan` | `scan` |
| Lidar odometrisi | `nav_msgs/Odometry` | `odom_rf2o` |
| Hız komutu | `geometry_msgs/Twist` | `cmd_vel`, `cmd_vel_nav` |
| Kamera karesi | `sensor_msgs/Image` | `camera/image_raw`, `camera/image_processed` |
| Harita | `nav_msgs/OccupancyGrid` | `map` |
| Sağlık/tanılama | `diagnostic_msgs/DiagnosticArray` | `/diagnostics` |
| Engel durumu | `std_msgs/Bool` | `obstacle_avoidance/blocked` |

İleride motor state/telemetri gibi gerçekten standart bir karşılığı olmayan
bir veri ortaya çıkarsa, o zaman özel bir `.msg` bu klasöre eklenir.
