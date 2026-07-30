# Sürücüler

## Sürücü Listesi

### Dahili / Gemstone kaynaklı
- **IMU**: ICM-20948, SPI `/dev/spidev0.3` — `gemstone_imu` paketi, T3
  Foundation'ın resmi C sürücü kütüphanesi (`icm20948.c/.h`) ile
- **GPIO (libgpiod)**: motor + enkoder + ultrasonik haberleşmesi
- **CSI kamera**: IMX219/OV5640, `v4l2_camera` ile — `gemstone_camera` paketi

### Harici
- `A1M8` RPLidar — USB üzerinden, Slamtec'in resmi `sllidar_ros2` paketiyle
- Harezmi motor+enkoder kartı (MX1508 H-bridge) — Gemstone GPIO'ları
  doğrudan bağlı (Deneyap sökülüp yerine geçildi), `gemstone_motor_driver`
  paketiyle (kinematik: diferansiyel sürüş, 2 tahrik teker + ön misket teker)
- HC-SR04 benzeri ultrasonik sensör(ler) — Gemstone GPIO, `gemstone_ultrasonic`
  paketiyle

## Sürücü Yaklaşımı

Her sürücü üç aşamada ele alınır:

1. düşük seviye init (SPI/GPIO/USB/CSI açma)
2. veri okuma / yazma
3. ROS topic çıkışı (standart mesaj tipleriyle, bkz. `interfaces/msg/README.md`)

## Dosya Organizasyonu

- `src/gemstone_*` - gerçek ROS 2 paketleri (sürücü + node kodu)
- `examples/` - gerçek paketlere işaret eden kısa notlar
- `hardware/` - bağlantı ve kablolama notları
- `tools/` - servis ve yardımcı scriptler (henüz boş)
- `interfaces/msg/` - mesaj tipi kararı
- `interfaces/ipc/` - köprü formatı (henüz kullanılmıyor)

## Not

Her sürücü, `docs/tr/quickstart.md`'deki "Kademeli Test" ile önce tek
başına, sonra `gemstone_bringup/launch/bringup.launch.py` içinde birlikte
doğrulanır.
