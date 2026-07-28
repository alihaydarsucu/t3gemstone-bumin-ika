# Sorun Giderme

## Sürücü başlamıyor

- device node var mı kontrol et
- izinleri ve `udev` kurallarını kontrol et
- log seviyesini yükselt
- servis sırasını doğrula

## Topic görünmüyor

- node çalışıyor mu?
- launch dosyası doğru parametrelerle açıldı mı?
- topic adı beklenen isimle mi yayınlanıyor?
- sensör gerçekten veri üretiyor mu?

## Kamera çalışmıyor

- sensör beslemesi
- USB / CSI bağlantısı
- frame formatı
- driver ve codec desteği

## Motor tepki vermiyor

- `/dev/ttyS0` (UART-WKUP0) izinleri ve fiziksel bağlantı doğru mu
- `gemstone_motor_driver/protocol.py`'deki çerçeve formatı, gerçek sürücü
  kartın beklediği protokolle eşleşiyor mu (bu hâlâ bir yer tutucu, bkz.
  `gemstone_ws/README.md` "Bilinen yer tutucular")
- `/cmd_vel` `cmd_vel_timeout` (varsayılan 0.5 sn) içinde geliyor mu — aksi
  halde node güvenlik gereği otomatik durur
- `ttyS3` kullanıyorsanız PWM overlay ile TX hattı çakışması olabilir, `ttyS6`
  kullanıyorsanız Bluetooth devre dışı kalır (bkz. T3 Gemstone seri port
  dokümantasyonu)

## IMU veri vermiyor

- `/dev/spidev0.3` erişimi/izinleri var mı
- `icm20948_driver_node`'un log'unda `icm20948_create`/`icm20948_configure`
  hatası var mı
- `/diagnostics` topic'inde `ICM-20948 IMU` durumu OK mi
