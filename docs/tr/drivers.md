# Sürücüler

## Sürücü Listesi

### Dahili / Gemstone kaynaklı
- **IMU**: ICM-20948, SPI `/dev/spidev0.3` — `gemstone_imu` paketi, T3
  Foundation'ın resmi C sürücü kütüphanesi (`icm20948.c/.h`) ile
- **UART**: `/dev/ttyS0` (UART-WKUP0) — motor sürücü kartla haberleşme
- **CSI kamera**: IMX219/OV5640, `v4l2_camera` ile — `gemstone_camera` paketi

### Harici
- `A1M8` RPLidar — USB üzerinden, Slamtec'in resmi `sllidar_ros2` paketiyle
- motor sürücü kartı — UART üzerinden, `gemstone_motor_driver` paketiyle
  (kinematik: diferansiyel sürüş, 2 tahrik teker + ön misket teker)

## Sürücü Yaklaşımı

Her sürücü üç aşamada ele alınır:

1. düşük seviye init (SPI/UART/USB/CSI açma)
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

Her sürücü, `gemstone_ws/README.md`'deki "Önerilen test sırası" ile önce tek
başına, sonra `gemstone_bringup/launch/bringup.launch.py` içinde birlikte
doğrulanır.
