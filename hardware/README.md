# Donanım Notları

Bu klasör pinout, bağlantı şeması ve harici modül notlarını içerir.

## Bilinen Bağlantılar (T3 Gemstone O1)

| Donanım | Arayüz | Yol / Not |
|---|---|---|
| Dahili IMU (ICM-20948) | SPI | `/dev/spidev0.3` (karta lehimlenmiş, ek kablolama yok) |
| Harezmi motor+enkoder kartı (MX1616H/MX1508 H-bridge) | GPIO (libgpiod) | Deneyap Kart sökülüp Gemstone GPIO'ları doğrudan bağlandı; güç harici 2S pilden, lojik Gemstone'un 3.3V+GND'sinden |
| Ultrasonik sensör(ler) (HC-SR04 benzeri) | GPIO (libgpiod, trig/echo) | Harezmi kartı üzerinden |
| RPLidar A1M8 | USB (dahili USB-seri) | `/dev/ttyUSB0`, 115200 baud |
| CSI kamera (IMX219/OV5640) | MIPI CSI0/CSI1 | device tree overlay + `gem-camera-setup` gerekir |

## Harezmi Motor+Enkoder Kartı Pin Haritası (eski Deneyap etiketleri, artık Gemstone GPIO'suna taşınıyor)

Kaynak: Harezmi-Deneyap entegrasyon dokümantasyonu (`Harezmi_Pin_Sayısı_..._Deneyap_entegrasyon_...pdf`),
multimetre ile doğrulandı.

| Fonksiyon | Eski Deneyap pini | Gemstone GPIO line (doldurulacak) |
|---|---|---|
| Motor 1 (sol) IN1 | D12 | `motor1_in1_line` |
| Motor 1 (sol) IN2 | D13 | `motor1_in2_line` |
| Motor 2 (sağ) IN1 | D14 | `motor2_in1_line` |
| Motor 2 (sağ) IN2 | D15 | `motor2_in2_line` |
| Enkoder 1 Kanal A (interrupt) | D2 | `encoder1_a_line` |
| Enkoder 1 Kanal B | D9 | `encoder1_b_line` |
| Enkoder 2 Kanal A (interrupt) | D3 | `encoder2_a_line` |
| Enkoder 2 Kanal B | A7 (D16) | `encoder2_b_line` |
| Ultrasonik 1 trig/echo | D0(A13) / D1(A12) | `ultrasonic1_trig_line` / `echo_line` |
| Ultrasonik 2 trig/echo | D7 / D8 | `ultrasonic2_trig_line` / `echo_line` |

Gerçek Gemstone GPIO line offsetleri karta bağlanıp `gpiodetect`/`gpioinfo`
ile bulunup `gemstone_bringup/params/motor_driver_params.yaml` ve
`ultrasonic_params.yaml` içine yazılacak.

## İçerik Alanları (henüz doldurulacak)

- Gemstone GPIO line offsetlerinin gerçek değerleri (yukarıdaki tablo)
- güç dağıtımı şeması (2S pil -> Harezmi kartı; Gemstone 3.3V+GND -> kart lojik beslemesi)
- fiziksel montaj ölçüleri (bkz. `gemstone_bringup/urdf/gemstone_ugv.urdf.xacro`
  içindeki yer tutucu ölçüler)
- PWM-uyumlu fiziksel pinler (değişken hız kontrolü için)

Kaynak: [docs.t3gemstone.org/tr/boards/o1](https://docs.t3gemstone.org/tr/boards/o1/introduction)
