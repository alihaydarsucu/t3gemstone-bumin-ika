# T3 Gemstone ROS Bringup - Blueprint

> Bu dosya projenin teknik omurgasını, kararlarını ve ilerleme kaydını tutar.
> Gemstone tarzına uygun şekilde kısa özet, sonra detaylı yapı kullanılır.

---

## Mimari Özet

```
T3 Gemstone O1 (tek kart)
├── A53 / Linux
│   ├── gemstone_imu             (ICM-20948, SPI /dev/spidev0.3)
│   ├── gemstone_motor_driver    (diferansiyel surus -> GPIO/libgpiod + enkoder odometrisi)
│   ├── gemstone_ultrasonic      (HC-SR04 benzeri mesafe sensoru, GPIO/libgpiod)
│   ├── gemstone_camera          (CSI kamera, v4l2_camera)
│   ├── gemstone_image_proc      (goruntu isleme iskeleti)
│   ├── gemstone_lidar_bringup   (sllidar_ros2 + rf2o + slam_toolbox + Nav2)
│   ├── gemstone_obstacle_avoidance (lidar tabanli guvenlik karari)
│   └── gemstone_bringup         (URDF + master launch)
└── Harici Sistemler
    ├── A1M8 RPLidar (USB)
    ├── Harezmi motor+enkoder karti (MX1508 H-bridge, Gemstone GPIO ile dogrudan surulur)
    ├── HC-SR04 benzeri ultrasonik sensor(ler) (Gemstone GPIO)
    └── CSI kamera (IMX219/OV5640)
```

Ayrı bir mikrodenetleyici (Deneyap vb.) **yok**; tüm sürücüler ve node'lar
tek kartın (Gemstone O1) Linux tarafında çalışır. Harezmi robotunun
motor+enkoder kartı üzerindeki Deneyap sökülüp yerine Gemstone'un GPIO'lari
dogrudan baglaniyor (guc: harici 2S pil motoru besliyor, Gemstone sadece
3.3V+GND ile kartin lojik tarafini besliyor).

---

## Temel Karar

- **Tek kart, tek Linux çalışma yüzeyi** — A53/Linux birincil ve tek katman
- **Motor kontrolü**: Gemstone, Harezmi kartindaki Deneyap'in yerini alarak
  motorlari (MX1508 H-bridge) VE kadratur enkoderleri **dogrudan GPIO
  uzerinden (libgpiod)** suruyor/okuyor. Bu, projenin ilk taslaginda
  degerlendirilen "harici karta UART ile komut gonderme" yaklasimindan
  **farkli** bir karardir -- gercek donanim (Harezmi + Deneyap pin haritasi)
  incelenince Gemstone'un dogrudan o karti surmesinin daha basit ve dogru
  oldugu goruldu, mimari buna gore guncellendi.
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
- `/dev/spidev0.3` (dahili IMU), GPIO/libgpiod (motor + enkoder + ultrasonik,
  Harezmi karti uzerinden), `/dev/ttyUSB0` (RPLidar USB-seri), CSI0/CSI1 (kamera)

### 2. Driver Layer
- `gemstone_imu`: ICM-20948 SPI sürücüsü (T3 Foundation'ın resmi C kütüphanesi)
- `gemstone_motor_driver`: diferansiyel sürüş kinematiği + GPIO (libgpiod)
  H-bridge sürücü + kadratür enkoder okuma + tekerlek odometrisi
- `gemstone_ultrasonic`: HC-SR04 benzeri sensör(ler), GPIO (libgpiod) trig/echo
- `gemstone_camera`: v4l2_camera launch (CSI, IMX219/OV5640)
- `sllidar_ros2` (third-party): RPLidar A1M8 sürücüsü

### 3. Node Layer
- `gemstone_image_proc`: görüntü işleme iskeleti (şu an passthrough)
- `gemstone_exploration_demo`: LiDAR + motion state verisiyle çalışan,
  timestamp kontrollü demo gezinti/planner davranışı
- `gemstone_motor_driver`: `/cmd_vel` -> motor GPIO sürüşü, isteğe bağlı
  encoder odometrisi ve IMU + wheel odom birleştiren hareket durumu yayını
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

Gerçek topic'ler:

- `/imu/data_raw`, `/imu/data` (Madgwick filtreli)
- `/cmd_vel`, `/cmd_vel_nav`
- `/wheel_odom` (enkoder tabanlı teker odometrisi)
- `/motion_state/odom`, `/motion_state/yaw`, `/motion_state/encoder_available`
- `/scan`, `/odom_rf2o` (lazer tabanlı odometri)
- `/cmd_vel_nav` (demo planner ve Nav2 çıkışı için ara komut)
- `/ultrasonic1/range`, `/ultrasonic2/range`
- `/obstacle_avoidance/blocked`
- `/camera/image_raw`, `/camera/image_processed`
- `/map`
- `/diagnostics`

> Not: Önceki taslakta önerilen `/gemstone/...` ön ekli topic isimleri
> (ör. `/gemstone/imu/data`) **kullanılmadı**. Bunun yerine `cmd_vel`, `scan`
> gibi ROS'un standart/varsayılan isimleri tercih edildi; böylece
> `teleop_twist_keyboard`, Nav2, `rqt` gibi hazır araçlar ek remap
> yapılmadan doğrudan çalışır.

> TF notu: `/wheel_odom` ve `/odom_rf2o` iki ayrı odometri KAYNAGIDIR;
> su an sadece rf2o (`publish_tf:true`) odom->base_link TF'ini yayinlar,
> `gemstone_motor_driver` yayinlamiyor (`publish_tf:false`) -- cakismayi
> onlemek icin. Ileride `robot_localization` (EKF) ile ikisini (+ IMU)
> birlestirip TEK bir TF kaynagi olusturmak en dogru yontem.

---

## Donanım Sınırları

- **Linux üzerinde tutulanlar**: kamera sürücüsü, kamera işleme, lidar
  bringup, motor kontrol yazılımı, launch orkestrasyonu — hepsi
- **RTOS/R5F**: bu sürümün kapsamı dışında (Gemstone'un R5F/NuttX çekirdeği
  kullanılmıyor); motor/enkoder GPIO işi de Linux userspace'te (libgpiod),
  R5F gerçek zamanlı çekirdeklere taşınmadı
- **PWM/hız kontrolü**: şu an motor sürücü sadece yön kontrolü yapıyor
  (bang-bang: tam hız/dur), gerçek değişken hız için Gemstone'un donanımsal
  PWM çıkışının hangi fiziksel pinlerde olduğu netleşmeli (bkz. roadmap)

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
- [x] motor GPIO sürücüsü + enkoder odometrisi (yön kontrolü hazır, PWM/hız
      kontrolü ve gerçek Gemstone GPIO pin numaraları netleşmeyi bekliyor)
- [x] ultrasonik mesafe sensörü (HC-SR04, GPIO)

### v0.3 - Orkestrasyon
- [x] tek launch dosyası (`gemstone_bringup/launch/bringup.launch.py`)
- [x] servis bağımlılıkları (her katman ayrı enable/disable argümanı)
- [ ] basit CLI seçimi
- [x] log / health çıktı sistemi (`diagnostic_updater`, `/diagnostics`)

### v0.4 - Donanım Genişleme
- [ ] Gemstone'un gerçek GPIO chip adı/line offsetlerinin (`gpiodetect`,
      `gpioinfo`) tespit edilip params dosyalarına yazılması
- [ ] motor/enkoder yön işaretlerinin (invert parametreleri) donanımla
      doğrulanması
- [ ] enkoder çözünürlüğünün (ticks_per_revolution) ölçülmesi
- [ ] PWM-uyumlu fiziksel pinlerin bulunup değişken hız kontrolünün eklenmesi
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
3. Motor sürücüsü Gemstone GPIO'larından (libgpiod) Harezmi kartindaki
   MX1508 H-bridge'i dogrudan surer, kadratur enkoderleri okur ve
   `/wheel_odom` yayinlar; kinematik/enkoder matematigi ayri, donanimsiz
   test edilebilir modullere bolunmustur (`differential_drive.py`,
   `quadrature_encoder.py`'deki `decode_tick_direction`).
4. CLI ve seçim arayüzü, tek launch akışının üstüne ileride eklenecek.

---

## Açık Sorular (cevaplandı)

Önceki taslaktaki açık sorular netleşti:

- **Kamera hangi Linux sürücü modeliyle bağlanacak?** → CSI (IMX219/OV5640),
  `v4l2_camera` ROS 2 paketiyle.
- **Lidar için ROS 2 paketi mi, özel node mu?** → Slamtec'in resmi
  `sllidar_ros2` paketi (özel sürücü yazılmadı).
- **Motor GPIO kontrolü doğrudan mı, küçük bir servisle mi?** → Dogrudan:
  Gemstone, Harezmi kartinin Deneyap'ini kaldirip motorlari ve enkoderleri
  kendi GPIO'larindan (libgpiod) suruyor/okuyor. Ilk taslakta dusunulen
  "harici karta UART ile komut" yaklasimi terk edildi.
- **Launch akışı yalnızca ROS 2 ile mi?** → Evet, `ros2 launch` tabanlı;
  ek bir servis yöneticisi (systemd vb.) şu an kullanılmıyor.

Kalan açık noktalar: Gemstone'un fiziksel GPIO pin/line eşlemesi ve PWM
desteği henüz donanımla tam doğrulanmadı (bkz. Yol Haritası v0.4).
