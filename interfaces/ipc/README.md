# IPC Sözleşmesi

Bu klasör, Linux tarafında çalışan paketler arasında hafif veri köprüsü veya ortak sözleşme notları için kullanılır.

## Amaç

- hafif veri aktarımı
- debug ve test için ortak format
- üst seviye servislerle entegrasyon

## Durum

Şu an tüm paketler arası iletişim doğrudan ROS 2 topic'leri üzerinden
yapılıyor (bkz. `interfaces/msg/README.md`); ek bir IPC katmanına ihtiyaç
duyulmadı. Tek istisna: `gemstone_motor_driver` ile harici motor sürücü kart
arasındaki UART çerçeve protokolü (`gemstone_motor_driver/protocol.py`) —
bu ROS dışı, donanıma özel bir sözleşme ve henüz gerçek kartla
doğrulanmadı.
