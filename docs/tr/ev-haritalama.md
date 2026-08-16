# Ev Dünyasında Otonom Haritalama (Simülasyon + Video Kaydı)

Bu doküman, `gemstone_frontier_explorer` paketinin ev dünyasında
(`house.world`) **Gazebo + RViz** üzerinden açılıp izlenmesini ve otonom
haritalama akışının çalıştırılmasını adım adım anlatır. Aynı akış video
kaydı için de kullanılır (bölüm 6).

## 1. Ön Koşullar

- Host: Linux + **Wayland** (GNOME Shell) + Docker. Bu projede host
  `XDG_SESSION_TYPE=wayland` çalışır; bu yüzden ekran kaydı için `ffmpeg
  x11grab` değil **GNOME Shell Screencast (DBus)** kullanılır (bkz. bölüm 6).
- Konteyner imajı `humble-turtlebot:latest` (ROS 2 Humble + Gazebo Classic).

## 2. Docker Konteyneri

İmajı oluşturun (ilk kez):

```bash
cd /home/ali/Desktop/t3gemstone-bumin-ika
docker build -t humble-turtlebot:latest .
```

Konteyneri oluşturup başlatın (host network, X11 paylaşımı):

```bash
xhost +local:
docker run -d --name gemstone_sim \
  --network=host \
  -e DISPLAY=:0 \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "$PWD:/ros_ws/src/t3gemstone-bumin-ika" \
  humble-turtlebot:latest
```

Zaten var olan bir konteyneri tekrar başlatmak için:

```bash
docker start gemstone_sim
```

> **DİKKAT (bind mount):** `$PWD:/ros_ws/src/t3gemstone-bumin-ika` **read-write**
> mount edilmiştir. Konteyner içinden bu yola `docker cp` ile yazmayın ve
> bu yol altında `rm -rf` yapmayın — host dosyalarını siler.
> Harita/kayıt çıktıları doğrudan bu bind mount üzerinden host'a düşer.

Konteyner içinde ortamı yükleyin:

```bash
docker exec -it gemstone_sim bash
# konteyner içinde:
cd /ros_ws
source /opt/ros/humble/setup.bash
```

## 3. Derleme

Konteyner içinde (yeni paket/parametre değişikliği sonrası):

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select \
  gemstone_sim gemstone_frontier_explorer gemstone_obstacle_avoidance \
  gemstone_lidar_bringup
source install/setup.bash
```

> `--symlink-install` sayesinde `src/*.launch.py`, `*.world`, `*.rviz`,
> `*.yaml` değişiklikleri install edilmiş kopyaya **anında** yansır;
> sadece C++/Python node kodları için rebuild gerekir.

## 4. Simülasyonu Başlatma (Gazebo + RViz)

Konteyner içinde, `DISPLAY=:0` ve `install/setup.bash` yüklü iken:

```bash
ros2 launch gemstone_frontier_explorer auto_mapping.launch.py \
  world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/house.world \
  enable_rviz:=true
```

Bu komut sırasıyla şunları başlatır:

1. `sim_bringup` → Gazebo (`house.world`, gravity `-20`), robot spawn
   (`-3.0, 2.0, 0.075`, yaw `1.5708`), `obstacle_avoidance_node`
   (`safety_distance: 0.25`), `motion_state`, kamera/işleme.
2. `lidar_bringup` → slam_toolbox (mapping) + Nav2 (DWB, `/cmd_vel_nav`).
3. `frontier_explorer_node` → frontier keşfi, Nav2 hedefleri.

**Doğrulama** — aşağıdaki pencereler açılmalı:
- **Gazebo**: ev + robot. (Yan yana değilse pencereyi kendiniz
  konumlandırabilirsiniz.)
- **RViz** (`auto_mapping.rviz` config'i otomatik yüklenir): Grid, TF,
  Map, LaserScan, Frontier Markers, RobotModel ve **CameraImage**
  (`/camera/image_raw`).

Robotun spawn olduğunu ve odometrisini kontrol edin:

```bash
ros2 topic echo /odom --once          # x ≈ -3.0, y ≈ 2.0, z ≈ 0.075
ros2 topic hz /scan                   # ~10 Hz
ros2 topic hz /camera/image_raw       # ~30 Hz
```

## 5. Otonom Haritalama Akışı

Kesife başlat:

```bash
ros2 service call /exploration/start std_srvs/srv/Trigger "{}"
# -> success=True message='Kesif basladi.'
```

İlerlemeyi izleyin:

```bash
ros2 topic echo /exploration/status --once
# data: RUNNING coverage=0.70 frontiers=8 goal_id=42 goal=(-6.5, -1.0)
```

Bittiğinde `NO_GOAL coverage=... frontiers=0` görülür. Robot evin tüm
ulaşılabilir bölgelerini dolaşmıştır.

Haritayı kaydet:

```bash
ros2 service call /exploration/save_map std_srvs/srv/Trigger "{}"
```

> Varsayılan konum repo kökü `map_son_*.pgm/.yaml`'dır (bind mount ile
> host'ta da görünür). İstediğiniz isimle kaydetmek için:
>
> ```bash
> ros2 run nav2_map_server map_saver_cli -f /tmp/house_map
> cp /tmp/house_map.pgm /tmp/house_map.yaml /ros_ws/src/t3gemstone-bumin-ika/
> ```

## 6. Video Kaydı (GNOME Shell Screencast)

Host **Wayland** olduğu için `ffmpeg -f x11grab` **çalışmaz**
(`Cannot get the image data ... error_code:128`). Bunun yerine GNOME
Shell'in DBus kayıt API'si kullanılır (VP8, 1920×1080 webm).

**Başlat** (host'ta, kaydı istenen dizinden):

```bash
cd /home/ali/Desktop/t3gemstone-bumin-ika/media
gdbus call --session \
  --dest org.gnome.Shell.Screencast \
  --object-path /org/gnome/Shell/Screencast \
  --method org.gnome.Shell.Screencast.Screencast \
  "/home/ali/Desktop/t3gemstone-bumin-ika/media/ev_mapping_%d.webm" \
  "{'framerate': <15>}"
# -> (true, '/home/ali/Desktop/t3gemstone-bumin-ika/media/ev_mapping_....webm')
```

**Kaydı durdur** (host'ta):

```bash
gdbus call --session \
  --dest org.gnome.Shell.Screencast \
  --object-path /org/gnome/Shell/Screencast \
  --method org.gnome.Shell.Screencast.StopScreencast
# -> (false,) dönmesi normaldir
```

**Doğrulama** (host'ta ffprobe yok; konteynerdeki ffprobe kullanılır):

```bash
docker cp <kayit.webm> gemstone_sim:/tmp/check.webm
docker exec gemstone_sim ffprobe -v error -show_entries \
  stream=codec_name,width,height -of default=noprint_wrappers=1 /tmp/check.webm
# codec_name=vp8, width=1920, height=1080
```

**Önerilen video akışı:**

1. Host'ta kaydı başlat (yukarıdaki `gdbus call`).
2. Bölüm 4'teki launch komutunu çalıştır → Gazebo + RViz açılır.
3. Bölüm 5'teki kesifi başlat ve `NO_GOAL frontiers=0` olana kadar izle.
4. Haritayı kaydet, kaydı durdur.

> Varsayılan GNOME Screencast pipeline'ı kullanılır; custom pipeline
> (`AllPipelinesFailed`) çalışmaz.

## 7. Sorun Çıkarırsa

- **Robot spawn olmuyor / "Entity already exists"**: tüm gazebo süreçlerini
  öldürüp yeniden başlatın:
  ```bash
  pkill -9 -f gzserver; pkill -9 -f gzclient; rm -rf ~/.gazebo/server-*
  ```
- **RViz config yüklenmiyor (parametreler yok)**: `-d` argümanı
  `rviz_config_file` launch arg'ından gelir; `enable_rviz:=true` olduğundan
  emin olun.
- **Kamera görüntüsü RViz'de boş**: `/camera/image_raw` yayında mı
  (`ros2 topic hz /camera/image_raw`)? Topic yoksa `sim_bringup` içindeki
  `image_processing_node` / gazebo kamera plugin'ini kontrol edin.
- **Robot çok sık takılıyor**: `obstacle_avoidance_node` `safety_distance`
  parametresi (`sim_bringup.launch.py`) 0.25; dar kapılarda 0.2'ye
  düşürülebilir.
- **Devrilme/ters dönme**: ev dünyasında gravity `-20` kullanılır; yine de
  olursa DWB `max_vel_x`/`acc_lim_x` değerlerini
  (`gemstone_lidar_bringup/params/nav2_params.yaml`) düşürün.
- **"Lidar verisi bayat" uyarıları**: `use_sim_time:=true` olduğundan emin
  olun.
