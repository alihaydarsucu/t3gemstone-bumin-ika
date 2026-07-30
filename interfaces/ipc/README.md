# IPC Sözleşmesi

Bu klasör, Linux tarafında çalışan paketler arasında hafif veri köprüsü veya ortak sözleşme notları için kullanılır.

## Amaç

- hafif veri aktarımı
- debug ve test için ortak format
- üst seviye servislerle entegrasyon

## Durum

Şu an tüm paketler arası iletişim doğrudan ROS 2 topic'leri üzerinden
yapılıyor (bkz. `interfaces/msg/README.md`); ek bir IPC katmanına ihtiyaç
duyulmadı. `gemstone_motor_driver` ve `gemstone_ultrasonic`, Harezmi
kartıyla ROS dışı bir protokol yerine doğrudan GPIO (libgpiod) üzerinden
konuşuyor -- bu da bir IPC sözleşmesi değil, donanım sürücü katmanı.
