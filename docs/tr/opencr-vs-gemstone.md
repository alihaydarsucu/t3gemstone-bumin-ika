# OpenCR ve Gemstone Karşılaştırması

Bu not, OpenCR yaklaşımını doğrudan kopyalamak yerine Gemstone üzerinde Linux-first bir ROS 2 bringup tasarlamak için hazırlanmıştır.

## Kısa Sonuç

- OpenCR, ROS için açık kaynak bir kontrol modülü olarak konumlanıyor ve donanım ile firmware tarafında açık bir ekosistem sunuyor.
- Gemstone, resmi dokümantasyona göre optimize edilmiş gerçek zamanlı Debian tabanlı GNU/Linux çalışan bir gelişim kartı.
- Gemstone dokümantasyonunda R5F/NuttX notları bulunsa da, bu repo tamamen Linux üzerinde çalışan ROS 2 node'larını esas alır.

Bu nedenle en doğru model:

1. açılışta Linux servislerini başlatmak
2. ROS 2 node'larını tek launch ile ayağa kaldırmak
3. sensör, lidar, kamera ve motor akışlarını topic tabanlı yönetmek

## OpenCR Tarafı

OpenCR, ROS odaklı açık kaynak bir kontrol modülü olarak tasarlanmıştır.
Donanım, firmware ve araç zinciri tarafında ROBOTIS ekosistemi içinde çalışır.

Bu modelin güçlü yanı:

- MCU tabanlı ve doğrudan kontrol odaklı olması
- robotik I/O için sade bir yayın mantığı sunması
- TurtleBot3 gibi sistemlerle doğal entegrasyon sağlaması

Bizim proje için önemli fikir şudur:

- cihaz açıldığında sürücüler hazır olsun
- sensör verisi otomatik olarak topic'e dönsün
- kullanıcı tek bir bringup komutuyla sistemi ayağa kaldırsın

## Gemstone Tarafı

Gemstone resmi dokümantasyona göre Linux tabanlı bir gelişim kartı olarak tanımlanıyor.
Quick Start ve Introduction sayfaları, sistemin SSH, serial, VNC ve system update akışlarıyla Linux üzerinde kullanıldığını gösteriyor.

Bu proje açısından önemli sonuç:

- sürücüler Linux kullanıcı alanında da rahatça organize edilebilir
- ROS 2 launch ve systemd ile otomatik başlatma doğal şekilde kurulabilir
- kamera, lidar ve sistem metrikleri aynı node ailesi altında toplanabilir

## Bu Proje İçin Mimari Karar

Bu repoda hedef:

- OpenCR'yi birebir taşımak değil
- OpenCR'nin "tak-çalıştır topic yayını" davranışını almak
- bunu Gemstone'un Linux mimarisiyle yapmak

Bu yüzden önerilen yapı:

- `systemd` ile bringup servisinin başlatılması
- `ros2 launch` ile sürücülerin ayağa kalkması
- her sensör için ayrı node
- topic isimlendirmesinin Gemstone odaklı standardize edilmesi

## Önerilen Proje Taslağı

### Çekirdek Paketler

- `gemstone_bringup`
- `gemstone_drivers`
- `gemstone_msgs`
- `gemstone_diagnostics`
- `gemstone_examples`

### Başlangıç Donanım Akışı

- Gemstone dahili sensörleri
- USB üzerinden `A1M8` RPLidar
- kamera sürücüsü
- harici motor sürücüsü
- sistem sağlık bilgileri

### Örnek Topic'ler

- `/gemstone/imu/data`
- `/gemstone/lidar/scan`
- `/gemstone/camera/image_raw`
- `/gemstone/motor/state`
- `/gemstone/system/diagnostics`

## Dokümantasyon Taslağı

Bu repo için önerilen sayfa sırası:

1. Tanıtım
2. Hızlı Başlangıç
3. Mimari
4. Sürücüler
5. Bringup
6. Topic Rehberi
7. Örnek Projeler
8. Geliştirme
9. Yol Haritası
10. SSS
11. Sorun Giderme

## Kaynaklar

- [OpenCR GitHub](https://github.com/ROBOTIS-GIT/OpenCR-Hardware)
- [OpenCR e-Manual](https://emanual.robotis.com/docs/en/parts/controller/opencr10/)
- [Gemstone Introduction](https://docs.t3gemstone.org/tr/introduction)
- [Gemstone Quick Start](https://docs.t3gemstone.org/en/quickstart)
- [Gemstone Development](https://docs.t3gemstone.org/tr/development)
- [Gemstone Serial Port](https://docs.t3gemstone.org/tr/boards/o1/peripherals/serial)
- [Gemstone NuttX](https://docs.t3gemstone.org/tr/projects/nuttx)
- [Gemstone Roadmap](https://docs.t3gemstone.org/tr/roadmap)
