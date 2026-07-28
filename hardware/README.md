# Donanım Notları

Bu klasör pinout, bağlantı şeması ve harici modül notlarını içerir.

## Bilinen Bağlantılar (T3 Gemstone O1)

| Donanım | Arayüz | Yol / Not |
|---|---|---|
| Dahili IMU (ICM-20948) | SPI | `/dev/spidev0.3` (karta lehimlenmiş, ek kablolama yok) |
| Motor sürücü kartı | UART (UART-WKUP0) | `/dev/ttyS0` — `ttyS2` konsol için ayrılmış, `ttyS6` Bluetooth'u kapatıyor, `ttyS3` PWM overlay ile çakışıyor |
| RPLidar A1M8 | USB (dahili USB-seri) | `/dev/ttyUSB0`, 115200 baud |
| CSI kamera (IMX219/OV5640) | MIPI CSI0/CSI1 | device tree overlay + `gem-camera-setup` gerekir |

## İçerik Alanları (henüz doldurulacak)

- motor sürücü kartın tam pinout'u ve güç gereksinimleri (kart modeli
  netleşince eklenecek)
- güç dağıtımı şeması (batarya -> regülatör -> kart/motor sürücü)
- fiziksel montaj ölçüleri (bkz. `gemstone_bringup/urdf/gemstone_ugv.urdf.xacro`
  içindeki yer tutucu ölçüler)

Kaynak: [docs.t3gemstone.org/tr/boards/o1](https://docs.t3gemstone.org/tr/boards/o1/introduction)
