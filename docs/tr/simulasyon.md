# Gazebo Simülasyonu

`gemstone_sim`, gerçek donanım yerine **Gazebo Classic** içinde çalışan
ofis dünyasında gemstone üst katman node'larını test eden simülasyon
paketidir. Donanım katmanlarının (motor sürücü, IMU, lidar, kamera)
yerini `gazebo_ros` plugin'leri alır; `motion_state`, `exploration_demo`,
`obstacle_avoidance` ve `image_processing` node'ları aynı topic
isimleriyle olduğu gibi çalışır.

## Kısa Video

Aşağıdaki video, simülasyonda UGV'nin ofis dünyasında gezinmesini gösterir
(tam dokümantasyon için
[13-simulasyon](https://github.com/alitalhq/t3gemstone-bumin-ika-docs/blob/main/docs/tr/13-simulasyon.md)
sayfasına bakın):

<video controls width="100%">
  <source src="https://raw.githubusercontent.com/alitalhq/t3gemstone-bumin-ika-docs/main/docs/assets/sim/sim-office-exploration.mp4" type="video/mp4">
  Tarayıcınız video etiketini desteklemiyor.
</video>

## Ön Koşullar

- ROS 2 Humble + Gazebo Classic içeren bir konteyner/imaj
  (örn. `humble-turtlebot:latest`; `gazebo_plugins` kurulu olmalı)
- Display erişimi: konteynere `DISPLAY` + `/tmp/.X11-unix` mount edilmiş
  olmalı ve host'ta `xhost +local:` yapılmış olmalı

## Derleme

```bash
# Konteyner içinde
cd /ros_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select gemstone_sim
source install/setup.bash
```

## Çalıştırma

```bash
ros2 launch gemstone_sim sim_bringup.launch.py
```

Rviz ile görmek isterseniz:

```bash
ros2 launch gemstone_sim sim_bringup.launch.py enable_rviz:=true
```

## Donanım → Simülasyon Eşlemesi

| Gerçek donanım | Simülasyondaki karşılığı | Topic |
|---|---|---|
| Motor sürücü | `libgazebo_ros_diff_drive` | `cmd_vel` → `odom` |
| RPLidar A1M8 | `libgazebo_ros_ray_sensor` (360 örnek, 3.5 m) | `scan` |
| IMU (ICM-20948) | `libgazebo_ros_imu_sensor` | `imu/data` |
| CSI kamera | `libgazebo_ros_camera` (640x480, 30 FPS) | `camera/image_raw` |
| Enkoder odometrisi | diff_drive `/odom` → `motion_state_node` | `wheel_odom` rolünde `odom` |

## Beklenen Veri Akışı

```
/imu/data ─┐
           ├─> motion_state_node ─> /motion_state/odom
/odom ─────┘                              │
                                          v
/scan ──────────────────> exploration_demo_node ─> /cmd_vel_nav
                                          │
/scan ──────────────────> obstacle_avoidance_node ─> /cmd_vel ─> gazebo
/camera/image_raw ─────> image_processing_node ─> /camera/image_processed
```

## Doğrulama

```bash
ros2 topic list
ros2 topic hz /scan               # ~10 Hz
ros2 topic hz /motion_state/odom  # ~90+ Hz
ros2 topic echo /cmd_vel          # robot hareket ederken sıfır değil
ros2 topic echo /motion_state/odom --once | grep -A2 position
```

Gazebo penceresinde robot ofis içinde dolaşıp engellerden kaçınmalı.

## Sorun Çıkarırsa

- **Robot spawn olmuyor / "Entity already exists"**: Önceki bir
  `gzserver` hâlâ çalışıyor olabilir. Tüm gazebo işlemlerini öldürüp
  yeniden başlatın:
  ```bash
  pkill -9 -f gzserver; pkill -9 -f gzclient; rm -rf ~/.gazebo/server-*
  ```
- **`/scan`, `/imu/data`, `/camera/image_raw` yayınlanmıyor**: Gazebo
  Classic, URDF `<link>` içindeki `<sensor>` etiketini okumaz; sensörler
  `<gazebo reference="link">` bloğunda tanımlı olmalı
  (bkz. `gemstone_ugv_gazebo.xacro`).
- **"Lidar verisi bayat" uyarıları**: `use_sim_time:=true` olduğundan
  emin olun; node'lar gerçek zaman yerine `/clock` kullanmalı.
