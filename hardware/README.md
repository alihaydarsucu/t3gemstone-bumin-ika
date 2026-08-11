# Donanım Notları

Bu klasör kısa pinout ve bağlantı özetleri içindir. Ayrıntılı dokümantasyon artık docs reposundadır.

> **[TR]** Kısa donanım notları burada kalır, uzun bağlantı rehberi docs reposuna taşındı.
>
> **[EN]** Short hardware notes stay here, while the long wiring guide lives in the docs repository.

## Hızlı Bağlantı

- [Türkçe dokümantasyon](https://docs.t3gemstone.org/tr/hardware)
- [English documentation](https://docs.t3gemstone.org/en/hardware)

## Kısa Özet

- IMU kart üzerinde SPI ile gelir.
- Motor akışı genel bir DC motor sürücüsü ile GPIO üzerinden sürülür; örnek şemada L298N kullanılmıştır, basit bir DC motor sürücüsü de aynı işi görür. Tekerlek enkoderi kullanılmıyor, hareket takibi IMU tabanlı `motion_state_node` ile yapılıyor.
- Ultrasonik sensörler yine GPIO ile okunur.
- Lidar USB seri üzerinden bağlanır.
- Kamera CSI üzerinden bağlanır.
