# Sürücüler

## Sürücü Listesi

### Dahili / Gemstone kaynaklı
- IMU
- UART
- GPIO
- PWM
- timer
- I2C / SPI / CAN
- USB / kamera
- sistem metrikleri

### Harici
- `A1M8` RPLidar
- motor sürücüsü
- kamera sensörü

## Sürücü Yaklaşımı

Her sürücü üç aşamada ele alınır:

1. düşük seviye init
2. veri okuma / yazma
3. ROS topic veya servis çıkışı

## Dosya Organizasyonu

- `examples/` - örnek bringup node'ları
- `hardware/` - bağlantı ve kablolama notları
- `tools/` - servis ve yardımcı scriptler
- `interfaces/msg/` - veri sözleşmeleri
- `interfaces/ipc/` - köprü formatı

## Not

Her sürücü için önce sade bir test node'u hazırlanır, sonra bringup içine alınır.
