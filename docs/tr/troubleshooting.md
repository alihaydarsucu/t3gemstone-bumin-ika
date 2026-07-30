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

- `gpio_chip` parametresi doğru mu (`gpiodetect` ile kontrol edin) — boşsa
  node hiç açılmaz (bilerek fail-fast)
- `motorN_in1_line`/`motorN_in2_line` gerçek line offsetleriyle eşleşiyor
  mu (`gpioinfo <chip>` ile kontrol edin) — varsayılan `-1` ise node açılmaz
- Harezmi kartındaki Deneyap gerçekten söküldü mü, Gemstone'un GPIO'ları
  doğru header pinlerine (D12/D13/D14/D15'in karşılığı) bağlandı mı
- `/cmd_vel` `cmd_vel_timeout` (varsayılan 0.5 sn) içinde geliyor mu — aksi
  halde node güvenlik gereği otomatik durur
- motor doğru yönde dönmüyorsa `motorN_invert` parametresini ters çevirin

## Enkoder tik saymıyor / yanlış yönde sayıyor

- `encoderN_a_line`/`encoderN_b_line` doğru mu (Kanal A interrupt-uyumlu
  bir pine bağlanmalı)
- Kanal A/B kabloları yer değiştirmiş olabilir — sayım hiç olmuyorsa Kanal A
  bağlantısını kontrol edin
- yön ters geliyorsa (motoru elle ileri çevirince tik sayacı azalıyorsa)
  `encoderN_invert` parametresini `true` yapın

## Ultrasonik sensör hep `inf` veya yanlış mesafe veriyor

- `gpio_chip`, `ultrasonicN_trig_line`/`echo_line` doğru mu
- trig ve echo kabloları yer değiştirmiş olabilir
- sensörün önünde gerçekten bir engel var mı, `min_range`/`max_range`
  dışında bir mesafe mi ölçülüyor

## IMU veri vermiyor

- `/dev/spidev0.3` erişimi/izinleri var mı
- `icm20948_driver_node`'un log'unda `icm20948_create`/`icm20948_configure`
  hatası var mı
- `/diagnostics` topic'inde `ICM-20948 IMU` durumu OK mi
