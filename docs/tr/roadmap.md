# Yol Haritası

## v0.1 - Taslak
- [x] repo adı ve klasör yapısı
- [x] temel README
- [x] blueprint
- [x] doküman indeksi

## v0.2 - Linux Temeli
- [x] board bringup (T3 Gemstone O1, ROS 2 Humble)
- [ ] systemd servis taslağı (şu an manuel `ros2 launch`)
- [x] ROS 2 launch iskeleti (`gemstone_bringup/launch/bringup.launch.py`)
- [x] publish helper (her paket kendi node'unda)

## v0.3 - Sürücüler
- [x] IMU (`gemstone_imu`, ICM-20948 SPI, T3 Foundation C kütüphanesi)
- [x] lidar (`gemstone_lidar_bringup`, sllidar_ros2 + rf2o_laser_odometry)
- [x] motor sürücüsü (`gemstone_motor_driver`, GPIO/libgpiod + enkoder
      odometrisi; gerçek pin numaraları henüz doğrulanmadı)
- [x] ultrasonik sensör (`gemstone_ultrasonic`, GPIO/libgpiod)
- [x] kamera sürücüsü (`gemstone_camera`, CSI + v4l2_camera)

## v0.4 - Örnekler
- [x] kamera işleme örneği (`gemstone_image_proc`, iskelet/passthrough)
- [x] lidar bringup örneği (`gemstone_lidar_bringup`)
- [ ] robot base örneği (URDF var, gerçek ölçüler eksik)
- [x] diagnostics / health node'u (`diagnostic_updater`, `/diagnostics`)

## v1.0 - Kullanılabilir Çekirdek
- [x] sensör topic'leri (IMU, lidar, kamera)
- [x] motor kontrol akışı (kod hazır, saha testi bekliyor)
- [x] kamera pipeline (iskelet hazır, gerçek CV görevi eksik)
- [x] güvenli kapanış / watchdog (motor cmd_vel timeout, obstacle avoidance
      fail-safe stale-scan davranışı)

## v1.1 - Saha Doğrulama (yeni)
- [ ] karta bağlanıp `colcon build` + tek tek node testi
- [ ] Gemstone'un gerçek GPIO chip adı/line offsetlerinin (`gpiodetect`,
      `gpioinfo`) tespit edilip params dosyalarına yazılması
- [ ] motor/enkoder yön işaretlerinin (invert parametreleri) doğrulanması
- [ ] enkoder çözünürlüğünün (ticks_per_revolution) ölçülmesi
- [ ] PWM-uyumlu fiziksel pinlerin bulunup değişken hız kontrolünün eklenmesi
- [ ] URDF ölçülerinin gerçek araçla güncellenmesi
- [ ] Nav2 `params.yaml`'ın tamamlanması (bkz. `nav2_overrides.md`)
- [ ] basit CLI / seçim arayüzü
