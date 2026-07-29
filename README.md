# T3 Gemstone Bumin İKA 

> **[TR]** T3 Gemstone O1 kartı üzerinde çalışan, diferansiyel sürüşlü (2 tahrik teker + ön misket teker) bir insansız kara aracı (İKA) için sensör, kamera, lidar ve motor akışlarını tek launch üzerinden ayağa kaldıran ve otonom sürüş kodlarını da içeren, uçtan uca bir ROS 2 Humble projesi. 
>
> **[EN]** A ROS 2 Humble project for a differential-drive (2 driven wheels + front caster) unmanned ground vehicle running on the T3 Gemstone O1 board, bringing up IMU, camera, lidar and motor workflows through a single launch flow, and including the full autonomous driving stack.

---

## Kısa Tanım

Bu repo, T3 Gemstone O1 kartı üzerinde **Linux-first bir ROS 2 bringup sistemi** kurar.
Tek kart tüm görevleri üstlenir: motor/teker sürme, dahili IMU okuma, lidar tabanlı
karar/harita/otonomi, kamera + görüntü işleme. Ayrı bir mikrodenetleyici (Deneyap
vb.) yok; motor sürücüsü harici bir sürücü karta UART üzerinden bağlanır.

Bringup hattı şunları yapar:

- `ICM-20948` dahili IMU'yu SPI (`/dev/spidev0.3`) üzerinden okuyup `imu/data_raw`
  yayınlar (T3 Foundation'ın resmi C sürücü kütüphanesiyle)
- `/cmd_vel`'i diferansiyel sürüş kinematiğiyle sol/sağ teker hızına çevirip UART
  üzerinden harici motor sürücü karta yazar
- CSI kamerayı (`v4l2_camera`) açıp `camera/image_raw` yayınlar
- `A1M8` RPLidar'ı Slamtec'in resmi `sllidar_ros2` paketiyle bağlar
- lidar verisiyle gerçek zamanlı engelden kaçınma, `slam_toolbox` ile haritalama
  ve Nav2 ile otonom navigasyon sağlar
- hepsini tek bir launch dosyasıyla (`gemstone_bringup/launch/bringup.launch.py`)
  başlatır

---

## Tasarım İlkesi

1. **A53 / Linux = ana çalışma katmanı** — kart üzerinde ayrı bir mikrodenetleyici
   yok, tüm sürücüler ve node'lar Gemstone'un Linux tarafında çalışır.
2. **Sürücü / node ayrımı** — her donanım için ayrı bir paket: `gemstone_imu`,
   `gemstone_motor_driver`, `gemstone_camera`, `gemstone_image_proc`,
   `gemstone_lidar_bringup`, `gemstone_obstacle_avoidance`.
3. **Standart ROS mesaj tipleri** — özel mesaj tipi icat etmek yerine
   `sensor_msgs`, `geometry_msgs`, `std_msgs`, `diagnostic_msgs` kullanılır; böylece
   teleop, rqt, Nav2, slam_toolbox gibi standart araçlarla doğrudan uyumlu olunur
   (bkz. [interfaces/msg/README.md](interfaces/msg/README.md)).
4. **Kademeli doğrulama** — her node önce tek başına test edilir, sonra hepsi
   `bringup.launch.py` altında birleştirilir (bkz.
   [docs/tr/quickstart.md](docs/tr/quickstart.md)).

---

## Repo Haritası

- `docs/` - proje dokümantasyonu
- `src/` - ROS 2 paketleri
  - `gemstone_imu` - ICM-20948 SPI sürücüsü (C++)
  - `gemstone_motor_driver` - diferansiyel sürüş + UART motor sürücüsü (Python)
  - `gemstone_camera` - CSI kamera launch (v4l2_camera)
  - `gemstone_image_proc` - görüntü işleme iskeleti
  - `gemstone_obstacle_avoidance` - lidar tabanlı güvenlik/karar node'u
  - `gemstone_lidar_bringup` - sllidar_ros2 + rf2o + slam_toolbox + Nav2
  - `gemstone_bringup` - URDF, ortak parametreler, master launch
- `examples/` - örnek senaryo notları (gerçek implementasyonlara işaret eder)
- `interfaces/` - mesaj ve IPC sözleşme kararları
- `hardware/` - bağlantı ve donanım notları
- `tools/` - CLI ve yardımcı script alanı (henüz boş)

---

## Durum

| Alan | Durum | Not |
|---|---:|---|
| Linux bringup | Calisiyor (henuz saha testi yok) | Tek launch, tum katmanlar ayri ac/kapa argumanli |
| IMU (ICM-20948) | Kod hazir | T3 Foundation C kutuphanesi + ROS 2 node |
| Motor surucu | Kod hazir, protokol yer tutucu | UART cercevesi gercek surucu kartla dogrulanmadi |
| Kamera (CSI) | Kod hazir | v4l2_camera ile |
| Goruntu isleme | Iskelet | Gercek CV gorevi henuz yok |
| RPLidar A1M8 | Kod hazir | sllidar_ros2 ile |
| Engelden kacinma | Kod hazir | Birim testleriyle dogrulandi |
| SLAM (slam_toolbox) | Kod hazir | Saha testi bekliyor |
| Nav2 | Launch hazir, params eksik | bkz. nav2_overrides.md |
| CLI / secim arayuzu | Planlandi | Sonraki faz |

Detaylı ilerleme için [docs/tr/roadmap.md](docs/tr/roadmap.md) ve
[docs/tr/revision.md](docs/tr/revision.md).

---

## Build

- Yerel kurulum notları için [docs/tr/build.md](docs/tr/build.md)
- Detaylı çalıştırma kılavuzu için [docs/tr/quickstart.md](docs/tr/quickstart.md)
- Hızlı ve izole deneme için kökteki `Dockerfile`
- Mimari kararlar için [BLUEPRINT.md](BLUEPRINT.md)
