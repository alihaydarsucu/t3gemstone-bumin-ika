# T3 Gemstone ROS Bringup

> **[TR]** T3 Gemstone üzerinde sensör, kamera, lidar ve motor akışlarını tamamen Linux tarafında çalışan ROS 2 node'larıyla tek launch üzerinden ayağa kaldıran geliştirme projesi.
>
> **[EN]** A T3 Gemstone development project that brings up the related sensor ROS nodes with a single launch flow and manages camera, lidar, and motor workflows in a modular way.

---

## Kısa Tanım

Bu repo, Gemstone üzerinde **Linux-first bir ROS bringup sistemi** kurmak için hazırlanmıştır.
Ana hedef, donanımı tek bir uygulama ailesi altında toplamak ve sistem başlangıcını tek komutla yönetmektir.

Şu anda bringup hattı:

- `ICM-20948` IMU verisini `/gemstone/imu/data` olarak yayınlar
- A1M8 lidar için Slamtec ROS 2 driver launch'unu açar
- sensörleri gerçek cihaz erişimiyle ayağa kaldırmayı hedefler

İlk sürümde odak şu şekildedir:

- Gemstone üzerindeki kart yazılımı ile birlikte çalışmak,
- sensör topic'lerini Linux üzerinde üretmek,
- kamerayı ve görüntü işleme örneğini Linux'ta çalıştırmak,
- `A1M8` RPLidar'ı USB üzerinden bağlamak,
- harici motor sürücüsünü GPIO, UART, CAN veya USB üzerinden yönetmek,
- hepsini aynı anda başlatan bir launch dosyası kullanmak.

---

## Tasarım İlkesi

1. **A53 / Linux = ana çalışma katmanı**
   - kamera sürücüsü
   - görüntü işleme node'u
   - lidar bringup
   - topic üretimi
   - launch yönetimi

2. **Topic odaklı tasarım**
   - her donanım için net topic sözleşmesi
   - launch ile birlikte kolay başlatma
   - CLI ve seçim arayüzüne uygun modüler yapı

3. **Kademeli mimari**
   - önce Linux'ta çalışan sürücü ve örnekler
   - sonra gerekiyorsa ek ROS paketleri ve servisler

---

## Hedef Kapsam

- Gemstone kart yazılımı ile uyumlu Linux tabanlı bringup
- Harici IKA projesi için
  - `A1M8` RPLidar via USB
  - kamera sürücüsü
  - kamera görüntü işleme örnek node'u
  - motor sürücüsü via GPIO, UART veya CAN
- Tek launch dosyası ile tüm bileşenleri başlatma
- Sonraki aşamada basit CLI ve seçim arayüzü
- Uzun vadede daha fazla ROS paketi, servis ve otomasyon ekleme

---

## Repo Haritası

- `docs/` - proje dokümantasyonu
- `src/` - ROS 2 paketleri ve uygulama kodu
- `src/gemstone_bringup/launch/` - ana launch akışı
- `examples/` - örnek senaryo notları
- `interfaces/` - mesaj ve IPC sözleşmeleri
- `hardware/` - bağlantı ve donanım notları
- `tools/` - CLI ve yardımcı script alanı

---

## Durum

Bu repo bir **Linux-first taslak başlangıç noktası**dır.
İçerik, geliştirme başlamadan önce modüler yapıyı ve tek katmanlı çalışma yolunu netleştirmek için hazırlanmıştır.

| Alan | Durum | Not |
|---|---:|---|
| Linux bringup | Taslak | A53 üzerinde ana akış |
| Kamera sürücüsü | Taslak | Linux'ta çalışacak |
| Kamera işleme örneği | Taslak | Basit görüntü işleme node'u |
| RPLidar A1M8 desteği | Taslak | USB üzerinden |
| Motor sürücü desteği | Taslak | GPIO üzerinden |
| Launch orkestrasyonu | Taslak | Tek komutla start |
| CLI / seçim arayüzü | Taslak | Sonraki faz |
| Ek ROS paketleri | Taslak | Lidar, kamera, motor ve diagnostic genişleme |

---

## Başlangıç Notu

Bu projenin ana amacı şudur:

> Gemstone üzerinde tek launch ile çalışan, sensör ve kamera topic'lerini Linux tarafında üreten bir ROS bringup altyapısı kurmak.

Bu yüzden doküman dili kısa, doğrudan ve geliştirmeye dönüktür.

---

## Build

- Yerel kurulum ve çalışma notları için [docs/tr/build.md](/home/ali/Projeler/t3-gemstone-ros-bringup/docs/tr/build.md)
- Hızlı ve izole deneme için kökteki `Dockerfile`
