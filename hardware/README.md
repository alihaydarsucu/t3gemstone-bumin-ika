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

| Fonksiyon | Eski Deneyap pini | Gemstone GPIO chip/line | GPIO adı | Fiziksel pin* |
|---|---|---|---|---|
| Motor 1 (sol) IN1 | D12 | `gpiochip3` / 7 | GPIO16 | 36 |
| Motor 1 (sol) IN2 | D13 | `gpiochip3` / 8 | GPIO17 | 11 |
| Motor 2 (sağ) IN1 | D14 | `gpiochip3` / 16 | GPIO12 | 32 |
| Motor 2 (sağ) IN2 | D15 | `gpiochip3` / 18 | GPIO13 | 33 |
| Enkoder 1 Kanal A (interrupt) | D2 | `gpiochip3` / 9 | GPIO21 | 40 |
| Enkoder 1 Kanal B | D9 | `gpiochip3` / 10 | GPIO20 | 38 |
| Enkoder 2 Kanal A (interrupt) | D3 | `gpiochip3` / 11 | GPIO18 | 12 |
| Enkoder 2 Kanal B | A7 (D16) | `gpiochip3` / 12 | GPIO19 | 35 |
| Ultrasonik 1 trig | D0(A13) | `gpiochip2` / 33 | GPIO27 | 13 |
| Ultrasonik 1 echo | D1(A12) | `gpiochip2` / 36 | GPIO26 | 37 |
| Ultrasonik 2 trig | D7 | `gpiochip2` / 41 | GPIO22 | 15 |
| Ultrasonik 2 echo | D8 | `gpiochip2` / 42 | GPIO25 | 22 |

`gemstone_bringup/params/motor_driver_params.yaml` ve `ultrasonic_params.yaml`
içine bu değerler (2026-07-30'da `gpiodetect`/`gpioinfo` çıktısıyla doğrulanarak)
yazıldı. Kasıtlı olarak KULLANILMAYAN pinler: GPIO2/GPIO3 (I2C), GPIO7/8/9/10/11
(SPI0 -- IMU `spidev0.3` bunu kullanıyor), GPIO4/14/15/17 (UART-MAIN1/UART-MAIN6
+ PWM overlay).

*Fiziksel pin numaraları, kartın "Raspberry Pi uyumlu" 40-pin header'ı
standart RPi BCM düzenini birebir takip ettiği varsayımıyla verilmiştir
(line isimleri zaten `GPIO16` gibi RPi adlandırmasıyla eşleşiyor). Kabloyu
bağlamadan önce kart üzerindeki "Pin 1" işaretiyle mutlaka görsel doğrulama
yapın.

## İçerik Alanları (henüz doldurulacak)

- güç dağıtımı şeması (2S pil -> Harezmi kartı; Gemstone 3.3V+GND -> kart lojik beslemesi)
- fiziksel montaj ölçüleri (bkz. `gemstone_bringup/urdf/gemstone_ugv.urdf.xacro`
  içindeki yer tutucu ölçüler)
- PWM-uyumlu fiziksel pinler (değişken hız kontrolü için)

Kaynak: [docs.t3gemstone.org/tr/boards/o1](https://docs.t3gemstone.org/tr/boards/o1/introduction)
