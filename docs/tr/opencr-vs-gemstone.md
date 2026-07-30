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

## Gerçekleşen Proje Yapısı

Aşağıdaki taslak, aşağıdaki gerçek paket bölünmesine evrildi (bkz.
`BLUEPRINT.md`):

### Çekirdek Paketler

- `gemstone_imu` — ICM-20948 SPI sürücüsü
- `gemstone_motor_driver` — diferansiyel sürüş + GPIO (libgpiod) motor
  sürücü + kadratür enkoder odometrisi
- `gemstone_ultrasonic` — HC-SR04 benzeri ultrasonik mesafe sensörü (GPIO)
- `gemstone_camera` / `gemstone_image_proc` — CSI kamera + görüntü işleme
- `gemstone_lidar_bringup` — sllidar_ros2 + rf2o + slam_toolbox + Nav2
- `gemstone_obstacle_avoidance` — lidar tabanlı güvenlik/karar node'u
- `gemstone_bringup` — URDF + master launch

Ayrı bir `gemstone_msgs` paketine gerek kalmadı: proje standart ROS mesaj
tiplerini kullanıyor (bkz. `interfaces/msg/README.md`).

### Başlangıç Donanım Akışı

- Gemstone dahili sensörleri (ICM-20948 IMU)
- USB üzerinden `A1M8` RPLidar (`sllidar_ros2`)
- CSI kamera sürücüsü (`v4l2_camera`)
- Harezmi motor+enkoder kartı, Gemstone GPIO'larıyla doğrudan sürülüyor
  (Deneyap sökülüp yerine geçildi)
- ultrasonik mesafe sensörü (GPIO)
- sistem sağlık bilgileri (`diagnostic_updater`)

### Gerçek Topic'ler

`/gemstone/...` ön eki yerine ROS'un standart/varsayılan isimleri
kullanılıyor (teleop/Nav2/rqt gibi hazır araçlarla uyumluluk için):

- `/imu/data_raw`, `/imu/data`
- `/scan`, `/odom_rf2o`, `/wheel_odom`
- `/ultrasonic1/range`, `/ultrasonic2/range`
- `/camera/image_raw`, `/camera/image_processed`
- `/cmd_vel`, `/cmd_vel_nav`
- `/diagnostics`

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
