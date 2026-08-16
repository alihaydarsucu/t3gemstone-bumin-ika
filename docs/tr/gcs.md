# Gemstone GCS — Tarayıcıda Yer Kontrol İstasyonu

Bu doküman, ev dünyası simülasyonunu **tarayıcıdan** izleyip yönetmenizi
sağlayan GCS (Ground Control Station) arayüzünü anlatır. Gazebo + RViz
açmak yerine `http://localhost:8000` açılır; harita, kamera, teleop ve
keşif kontrolü tek sayfadan yapılır.

## 1. Mimari

```
Gemstone sim (konteyner, host network)
   │
   ├─ rosbridge_websocket :9090  <-> tarayıcı (roslib.js, JSON/WS)
   │      - topic aboneliği: /map, /odom, /exploration/*
   │      - servis çağrısı:  /exploration/start|stop|save_map
   ├─ web_video_server  :8080  <-> <img> MJPEG akışı (/camera/image_raw)
   ├─ http.server       :8000  <-> statik web arayüzü (gcs/ dizini)
   └─ auto_mapping      (Gazebo + slam_toolbox + Nav2 + frontier explorer)
```

Bileşenler ROS 2 Humble apt paketleriyle gelir (`rosbridge_server`,
`web_video_server`, `rosapi`) — ek kurulum gerekmez. Web arayüzü
`gemstone_gcs` paketinin `gcs_bringup.launch.py`'sinden servis edilir.

## 2. Başlatma

Konteyner çalışıyorsa (`docker start gemstone_sim`):

```bash
docker exec -it gemstone_sim bash
cd /ros_ws && source /opt/ros/humble/setup.bash && source install/setup.bash

ros2 launch gemstone_gcs gcs_bringup.launch.py
```

> Varsayılan `world_file` office.world'dir. Ev dünyası için:
>
> ```bash
> ros2 launch gemstone_gcs gcs_bringup.launch.py \
>   world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/house.world
> ```

Launch, `auto_mapping.launch.py`'yi (Gazebo + robot + Nav2 + explorer)
**rviz kapalı** olarak başlatır — görüntü zaten web tarafında.

Tarayıcıda **http://localhost:8000** açın, host/port doğruysa (varsayılan
`localhost:9090`) **Bağlan**'a basın.

## 3. Paneller

| Panel | Kaynak | Açıklama |
|-------|--------|----------|
| Harita | `/map` + `/odom` | OccupancyGrid çizilir; robot mavi ok, frontier'ler yeşil nokta, hedef turuncu ok. |
| Kamera | `/camera/image_raw` (MJPEG) | Topic alanı değiştirilebilir, "Akışı Aç" yeniler. |
| Teleop | `/cmd_vel` | Butonlar veya klavye (WASD / ok tuşları, boşluk durdur). Hız/dönüş sürgülerle. **Dikkat:** `/cmd_vel`'e doğrudan yazar, güvenlik katmanını bypass eder. |
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

## 5. Sorun Çıkarırsa

- **"Bağlantı hatası"**: rosbridge süreci çalışıyor mu?
  `ps aux | grep rosbridge`. Port açık mı? `(exec 3<>/dev/tcp/127.0.0.1/9090)`.
- **Kamera siyah**: `web_video_server` çalışıyor ve topic yayında mı?
  `ros2 topic hz /camera/image_raw`. Topic adı panelde doğru mu?
- **Port çakışması**: portlar launch arg'larıyla değiştirilebilir:
  `rosbridge_port:=9090 video_port:=8080 web_port:=8000`.
- **Harita gelmiyor**: slam_toolbox `/map` yayınlıyor mu?
  `ros2 topic hz /map`. İlk saniyelerde boş görünebilir.
- **RViz istemiyorum, sadece web**: `gcs_bringup` rviz'i hiç açmaz
  (`enable_rviz:=false` içten iletilir).

## 6. Dosyalar

- `gcs/index.html` — arayüz yapısı (paneller, butonlar).
- `gcs/gcs.js` — roslib.js bağlantısı, harita çizimi, teleop, servis çağrıları.
- `gcs/gcs.css` — koyu tema.
- `gcs/vendor/roslib.js` — indirilen roslib.js (internet bağımlılığı yok).
- `src/gemstone_gcs/launch/gcs_bringup.launch.py` — rosbridge + web_video_server
  + http.server + auto_mapping'i başlatan launch.
