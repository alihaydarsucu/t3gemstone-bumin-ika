# T3 Gemstone ROS Bringup - Blueprint

> Bu dosya projenin teknik omurgasını, kararlarını ve ilerleme kaydını tutar.
> Gemstone tarzına uygun şekilde kısa özet, sonra detaylı yapı kullanılır.

---

## Mimari Özet

```
T3 Gemstone O1 (tek kart)
├── A53 / Linux
│   ├── gemstone_imu             (ICM-20948, SPI /dev/spidev0.3)
│   ├── gemstone_motor_driver    (diferansiyel surus -> UART)
│   ├── gemstone_camera          (CSI kamera, v4l2_camera)
│   ├── gemstone_image_proc      (goruntu isleme iskeleti)
│   ├── gemstone_lidar_bringup   (sllidar_ros2 + rf2o + slam_toolbox + Nav2)
│   ├── gemstone_obstacle_avoidance (lidar tabanli guvenlik karari)
│   └── gemstone_bringup         (URDF + master launch)
└── Harici Sistemler
    ├── A1M8 RPLidar (USB)
    ├── Motor surucu kart (UART)
    └── CSI kamera (IMX219/OV5640)
```

Ayrı bir mikrodenetleyici (Deneyap vb.) **yok**; tüm sürücüler ve node'lar
tek kartın (Gemstone O1) Linux tarafında çalışır.

---

## Temel Karar

- **Tek kart, tek Linux çalışma yüzeyi** — A53/Linux birincil ve tek katman
- **Motor kontrolü**: Linux'tan (ROS node) UART üzerinden harici bir motor
  sürücü karta komut gönderilir. GPIO'dan doğrudan sürme **tercih edilmedi**
  çünkü ekip harici sürücü kart + UART protokolüne karar verdi (bkz. Açık
  Sorular'ın cevaplandığı bölüm).
- **Sürüş tipi**: diferansiyel sürüş (2 bağımsız tahrik tekeri + önde pasif
  misket/caster teker). Ackermann/RC araba tipi değil.
- **Launch dosyası ile tüm bileşenler aynı anda başlar**, her katman ayrı
  ac/kapa argümanıyla (bkz. `docs/tr/bringup.md`)
- **Standart ROS mesaj tipleri kullanılır** (özel `.msg` yok), bkz.
  `interfaces/msg/README.md`

---

## Katmanlar

### 1. Board / Platform Layer
- T3 Gemstone O1 (TI AM67A, Ubuntu/Debian tabanlı gerçek zamanlı çekirdek)
- `/dev/spidev0.3` (dahili IMU), `/dev/ttyS0` (motor UART, UART-WKUP0),
  `/dev/ttyUSB0` (RPLidar USB-seri), CSI0/CSI1 (kamera)

### 2. Driver Layer
- `gemstone_imu`: ICM-20948 SPI sürücüsü (T3 Foundation'ın resmi C kütüphanesi)
- `gemstone_motor_driver`: diferansiyel sürüş kinematiği + UART çerçeve kodlayıcı
- `gemstone_camera`: v4l2_camera launch (CSI, IMX219/OV5640)
- `sllidar_ros2` (third-party): RPLidar A1M8 sürücüsü

### 3. Node Layer
- `gemstone_image_proc`: görüntü işleme iskeleti (şu an passthrough)
- `gemstone_obstacle_avoidance`: `/scan`'e bakıp ileri hızı sınırlayan karar node'u
- `slam_toolbox` (third-party): online haritalama
- `nav2_bringup` (third-party): otonom navigasyon

### 4. Orchestration Layer
- `gemstone_bringup/launch/bringup.launch.py`: her katman için ayrı
  enable/disable launch argümanı
- Test sırası: önce her node tek başına, sonra hepsi birlikte
  (bkz. `docs/tr/quickstart.md`)
- CLI / seçim arayüzü: henüz yok, sonraki faz

---

## Mesajlaşma İlkesi

Uygulanan yaklaşım:

- her cihaz için ayrı topic
- sürücü ve işleme node'u ayrımı
- standart ROS mesaj tipleri (özel `.msg` icat edilmedi)

Gerçek topic'ler (bkz. `gemstone_ws/README.md` için tam tablo):

- `/imu/data_raw`, `/imu/data` (Madgwick filtreli)
- `/cmd_vel`, `/cmd_vel_nav`
- `/scan`, `/odom_rf2o`
- `/obstacle_avoidance/blocked`
- `/camera/image_raw`, `/camera/image_processed`
- `/map`
- `/diagnostics`

> Not: Önceki taslakta önerilen `/gemstone/...` ön ekli topic isimleri
> (ör. `/gemstone/imu/data`) **kullanılmadı**. Bunun yerine `cmd_vel`, `scan`
> gibi ROS'un standart/varsayılan isimleri tercih edildi; böylece
> `teleop_twist_keyboard`, Nav2, `rqt` gibi hazır araçlar ek remap
> yapılmadan doğrudan çalışır.

---

## Donanım Sınırları

- **Linux üzerinde tutulanlar**: kamera sürücüsü, kamera işleme, lidar
  bringup, motor kontrol yazılımı, launch orkestrasyonu — hepsi
- **RTOS/R5F**: bu sürümün kapsamı dışında (Gemstone'un R5F/NuttX çekirdeği
  kullanılmıyor)

---

## Yol Haritası

### v0.1 - Linux Temeli
- [x] isim ve klasör yapısı
- [x] proje README
- [x] blueprint
- [x] doküman indeks yapısı
- [x] build sistemi seçimi (colcon + ROS 2 Humble)
- [x] launch iskeleti

### v0.2 - Linux Node'ları
- [x] kamera sürücüsü (v4l2_camera launch)
- [x] kamera işleme örneği (iskelet, gerçek CV görevi bekliyor)
- [x] lidar bringup (sllidar_ros2 + rf2o)
- [x] motor UART sürücüsü (protokol yer tutucu, gerçek kartla doğrulanmadı)

### v0.3 - Orkestrasyon
- [x] tek launch dosyası (`gemstone_bringup/launch/bringup.launch.py`)
- [x] servis bağımlılıkları (her katman ayrı enable/disable argümanı)
- [ ] basit CLI seçimi
- [x] log / health çıktı sistemi (`diagnostic_updater`, `/diagnostics`)

### v0.4 - Donanım Genişleme
- [ ] gerçek motor sürücü kartın UART protokolüyle doğrulama
- [ ] diagnostics genişletme
- [ ] saha testleri (kart üzerinde `colcon build` + tek tek node testi)
- [ ] Nav2 `params.yaml`'ın gerçek araç ölçüleriyle tamamlanması

---

## Teknik Notlar

1. Kamera sürücüsü ve görüntü işleme örneği aynı repo içinde ama farklı
   paketler olarak tutulur (`gemstone_camera` / `gemstone_image_proc`).
2. Lidar USB üzerinden yönetilir; bringup tek launch ile başlatılır
   (`gemstone_lidar_bringup/launch/lidar_bringup.launch.py`), her katman
   (`enable_rplidar`, `enable_rf2o`, `enable_slam_toolbox`, `enable_nav2`,
   `enable_obstacle_avoidance`) ayrı açılıp kapanabilir.
3. Motor sürücüsü Linux'tan UART üzerinden harici bir sürücü karta komut
   gönderir; kinematik ve seri çerçeve kodlama ayrı, donanımsız test
   edilebilir modüllere bölünmüştür (`differential_drive.py`, `protocol.py`).
4. CLI ve seçim arayüzü, tek launch akışının üstüne ileride eklenecek.

---

## Açık Sorular (cevaplandı)

Önceki taslaktaki açık sorular netleşti:

- **Kamera hangi Linux sürücü modeliyle bağlanacak?** → CSI (IMX219/OV5640),
  `v4l2_camera` ROS 2 paketiyle.
- **Lidar için ROS 2 paketi mi, özel node mu?** → Slamtec'in resmi
  `sllidar_ros2` paketi (özel sürücü yazılmadı).
- **Motor GPIO kontrolü doğrudan mı, küçük bir servisle mi?** → Ne biri ne
  öbürü: motor, Linux'taki bir ROS node'undan (`gemstone_motor_driver`)
  UART üzerinden harici bir sürücü karta komut göndererek çalışır. GPIO'dan
  doğrudan sürme bu proje için tercih edilmedi.
- **Launch akışı yalnızca ROS 2 ile mi?** → Evet, `ros2 launch` tabanlı;
  ek bir servis yöneticisi (systemd vb.) şu an kullanılmıyor.

Kalan açık nokta: motor sürücü kartın gerçek UART çerçeve protokolü henüz
donanımla doğrulanmadı (bkz. `gemstone_motor_driver/protocol.py` içindeki not).
