# Gemstone GCS — Tarayıcıda Yer Kontrol İstasyonu

Bu doküman, simülasyonu **tarayıcıdan** izleyip yönetmenizi sağlayan GCS
(Ground Control Station) arayüzünü anlatır. Gazebo + RViz açmak yerine
`http://localhost:8000` açılır; harita, kamera, teleop ve keşif kontrolü tek
sayfadan yapılır.

## 1. Mimari

```
Gemstone sim (konteyner, host network)
   │
   ├─ [ROBOT TARAFI] auto_mapping.launch.py
   │     Gazebo + slam_toolbox + Nav2 + frontier explorer + RViz
   │
   └─ [GCS TARAFI] gcs_bringup.launch.py
         ├─ rosbridge_websocket :9090  <-> tarayıcı (roslib.js, JSON/WS)
         │      - topic aboneliği: /map, /odom, /exploration/*
         │      - servis çağrısı:  /exploration/start|stop|save_map
         ├─ web_video_server  :8080  <-> <img> MJPEG akışı (/camera/image_raw)
         └─ http.server       :8000  <-> statik web arayüzü (gcs/ dizini)
```

İki taraf **ayrı launch dosyaları** olarak başlatılır — gerçek hayatta GCS
ayrı bir bilgisayarda çalışır ve robotla ROS graph üzerinden
(ROS_DOMAIN_ID / DDS) haberleşir. Bileşenler ROS 2 Humble apt paketleriyle
gelir (`rosbridge_server`, `web_video_server`, `rosapi`) — ek kurulum gerekmez.

## 2. Başlatma

Konteyner çalışıyorsa (`docker start gemstone_sim`) host tarafından kolay
yol — `tools/gcs.sh` (paste yarışını da önler):

```bash
./tools/gcs.sh robot                 # robot tarafı: sim + Nav2 + keşif + RViz (office.world)
./tools/gcs.sh robot house           # ev dünyası ile
./tools/gcs.sh web                   # GCS web tarafı (ayrı terminalde)
./tools/gcs.sh both                  # robot'u arka planda, web'i önde başlatır
```

Manuel (konteyner içinden, iki ayrı terminal):

```bash
# Terminal 1 — robot tarafı (RViz + sim + Nav2 + keşif):
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 launch gemstone_frontier_explorer auto_mapping.launch.py

# Terminal 2 — GCS web tarafı:
ros2 launch gemstone_gcs gcs_bringup.launch.py
```

> Varsayılan `world_file` office.world'dir. Ev dünyası için:
>
> ```bash
> ros2 launch gemstone_frontier_explorer auto_mapping.launch.py \
>   world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/house.world
> ```

Tarayıcıda **http://localhost:8000** açın, host/port doğruysa (varsayılan
`localhost:9090`) **Bağlan**'a basın.

## 3. Paneller

| Panel | Kaynak | Açıklama |
|-------|--------|----------|
| Harita | `/map` + `/odom` | OccupancyGrid çizilir; robot mavi ok, frontier'ler yeşil nokta, hedef turuncu ok. |
| Kamera | `/camera/image_raw` (MJPEG) | Topic alanı değiştirilebilir, "Akışı Aç" yeniler. |
| Teleop | `/cmd_vel_nav` | Önce **Klavye Kontrolünü Aç** butonuna basın, sonra ok tuşları / WASD ile sürün (boşluk durdur). Hız/dönüş sürgülerle ayarlanır. `/cmd_vel_nav`'e yazar → obstacle_avoidance güvenlik katmanından geçer. |
| Keşif | `/exploration/*` servisleri | "Kesife Basla" / "Durdur" / "Harita Kaydet". |

Durum satırı `/exploration/status` (RUNNING/DONE/IDLE) ve
`/exploration/coverage` (keşfedilen oran %) gösterir.

## 4. Doğrulama (komut satırı)

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/index.html   # 200
curl -s -o /dev/null -w '%{http_code}\n' \
  'http://localhost:8080/stream?topic=/camera/image_raw'                     # akış
# websocket: rosbridge 9090'a HTTP/1.1 101 Switching Protocols yanıtı
```

Robot tarafından tek başına:

```bash
ros2 topic hz /map                 # slam_toolbox harita yayınlıyor mu?
ros2 lifecycle get /bt_navigator   # active [3] olmalı
ros2 service call /exploration/start std_srvs/srv/Trigger "{}"
```

## 5. Sorun Çıkarırsa

- **"Bağlantı hatası"**: rosbridge süreci çalışıyor mu?
  `ps aux | grep rosbridge`. Port açık mı? `(exec 3<>/dev/tcp/127.0.0.1/9090)`.
- **Harita gelmiyor**: robot tarafı çalışıyor mu, slam_toolbox `/map`
  yayınlıyor mu? `ros2 topic hz /map`.
- **Klavye çalışmıyor**: **Klavye Kontrolünü Aç** butonuna basıldı mı?
  Sayfada input alanı odaklıysa tuşlar input'a gider.
- **Kamera siyah**: `web_video_server` çalışıyor ve topic yayında mı?
  `ros2 topic hz /camera/image_raw`. Topic adı panelde doğru mu?
- **Port çakışması**: portlar launch arg'larıyla değiştirilebilir:
  `rosbridge_port:=9090 video_port:=8080 web_port:=8000`.
- **RViz istemiyorum**: robot tarafını `enable_rviz:=false` ile başlatın.

## 6. Dosyalar

- `gcs/index.html` — arayüz yapısı (paneller, butonlar).
- `gcs/gcs.js` — roslib.js bağlantısı, harita çizimi, teleop, servis çağrıları.
- `gcs/gcs.css` — koyu tema.
- `gcs/vendor/roslib.js` — indirilen roslib.js (internet bağımlılığı yok).
- `src/gemstone_gcs/launch/gcs_bringup.launch.py` — **web tarafı** launch'ı
  (rosbridge + web_video_server + http.server).
- `src/gemstone_frontier_explorer/launch/auto_mapping.launch.py` —
  **robot tarafı** launch'ı (Gazebo + Nav2 + keşif + RViz).
- `tools/gcs.sh` — robot/web/both modlarıyla host tarafı başlatma.
