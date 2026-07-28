# T3 Gemstone ROS Bringup - Blueprint

> Bu dosya projenin teknik omurgasını, kararlarını ve ilerleme kaydını tutar.
> Gemstone tarzına uygun şekilde kısa özet, sonra detaylı yapı kullanılır.

---

## Mimari Özet

```
T3 Gemstone
├── A53 / Linux
│   ├── Kamera sürücüsü
│   ├── Kamera işleme örneği
│   ├── RPLidar A1M8 USB bringup
│   ├── Motor GPIO sürüşü
│   └── Topic / launch orkestrasyonu
└── Harici Sistemler
    ├── A1M8 RPLidar
    ├── Motor sürücüsü
    ├── Kamera
    └── Robot gövdesi sensörleri
```

---

## Temel Karar

Bu projede ana karar şu şekildedir:

- **İlk hedef Linux üzerinde çalışan tam bringup**
- **A53 tarafı birincil çalışma yüzeyi**
- **Motor kontrolü Linux node'ları ve servisleri ile başlar**
- **Launch dosyası ile tüm bileşenler aynı anda başlar**
- **Sonraki aşamada CLI ve seçim arayüzü eklenir**

Bu karar, geliştirmeyi hızlandırır ve saha testlerini kolaylaştırır.

---

## Katmanlar

### 1. Board / Platform Layer
- Gemstone kart yazılımı entegrasyonu
- port / device discovery
- USB cihaz eşleme
- GPIO erişimi
- servis bağımlılıkları

### 2. Driver Layer
- kamera sürücüsü
- lidar sürücüsü
- motor GPIO kontrolü
- power / battery / diagnostics

### 3. Node Layer
- kamera görüntü işleme node'u
- lidar bringup node'u
- motor kontrol node'u
- telemetri / sağlık node'u

### 4. Orchestration Layer
- launch dosyası
- servis başlatma sırası
- opsiyonel CLI seçim akışı
- ileride TUI / basit UI

---

## Mesajlaşma İlkesi

Önerilen yaklaşım:

- her cihaz için ayrı topic grubu
- sürücü ve işleme node'u ayrımı
- topic isimlerinde Gemstone / robot / modül ayrımı

Örnek topic'ler:

- `/gemstone/camera/image_raw`
- `/gemstone/camera/image_processed`
- `/gemstone/lidar/scan`
- `/gemstone/motor/state`
- `/gemstone/motor/cmd`
- `/gemstone/system/diagnostics`

---

## Donanım Sınırları

Bu repo aşağıdaki alanları ayrı ele alır:

- **Linux üzerinde tutulacaklar**
  - kamera sürücüsü
  - kamera işleme
  - lidar bringup
  - motor kontrol yazılımı
  - launch orkestrasyonu

Bu yaklaşım, sistemi tek ve açık bir Linux çalışma hattında tutar.

---

## Yol Haritası

### v0.1 - Linux Temeli
- [x] isim ve klasör yapısı
- [x] proje README
- [x] blueprint
- [x] doküman indeks yapısı
- [ ] build sistemi seçimi
- [ ] launch iskeleti

### v0.2 - Linux Node'ları
- [ ] kamera sürücüsü
- [ ] kamera işleme örneği
- [ ] lidar bringup
- [ ] motor GPIO kontrolü

### v0.3 - Orkestrasyon
- [ ] tek launch dosyası
- [ ] servis bağımlılıkları
- [ ] basit CLI seçimi
- [ ] log / health çıktı sistemi

### v0.4 - Donanım Genişleme
- [ ] kartın kendi yazılımı ile birlikte çalışma
- [ ] diagnostics genişletme
- [ ] saha testleri

---

## Teknik Notlar

1. Kamera sürücüsü ve görüntü işleme örneği aynı repo içinde ama farklı paketler olarak tutulur.
2. Lidar USB üzerinden yönetilir; bringup tek launch ile başlatılır.
3. Motor sürücüsü başlangıçta Linux + GPIO ile çalışır.
4. CLI ve seçim arayüzü, tek launch akışının üstüne eklenir.

---

## Açık Sorular

- Kamera hangi Linux sürücü modeliyle bağlanacak?
- Lidar için ROS 2 paketi mi, özel node mu kullanılacak?
- Motor GPIO kontrolü doğrudan kullanıcı uzayından mı, yoksa küçük bir servisle mi yürütülecek?
- Launch akışı yalnızca ROS 2 ile mi, yoksa ek servis yöneticisiyle mi çalışacak?

Bu sorular repo ilerledikçe netleştirilir.
