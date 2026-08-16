# Nav2 parametreleri hakkinda not

`nav2_params.yaml` artik repoda **mevcut ve guncel**: Humble stok
`nav2_bringup` `params/nav2_params.yaml` dosyasindan turetilmis, bu projeye
ozel degisikliklerle birlikte `gemstone_lidar_bringup/params/nav2_params.yaml`
olarak tutuluyor ve `lidar_bringup.launch.py` / `auto_mapping.launch.py`
tarafindan kullaniliyor.

## Projeye ozel yapilan degisiklikler

- `controller_server` DWB: `max_vel_x: 0.22`, `max_vel_theta: 0.6`,
  `acc_lim_x: 1.2`, `acc_lim_theta: 1.5` — dar/hafif robot mobilya
  bacaklarina carptiginda ters dönmesin diye dusuruldu
  (bkz. `docs/tr/ev-haritalama.md`).
- `robot_base_frame: base_link`, `robot_radius` costmap'lerde robot
  yaricapina gore ayarli.
- `odom_topic` Nav2'ye **launch argumani** ile verilir:
  - Donanim: `/odom_rf2o` (rf2o_laser_odometry)
  - Gazebo sim: `/odom` (diff_drive)
- Diferansiyel surus oldugumuz icin controller plugin olarak
  `DWB` kullaniliyor.
- `map_server` / `map_saver` / `amcl` / `velocity_smoother` baslatilmiyor:
  haritayi slam_toolbox `/map` saglar, harita kaydini
  `frontier_explorer_node`'un `/exploration/save_map` servisi yapar, hiz
  guvenligini `obstacle_avoidance_node` yapar.

## Degisiklik akisi

Parametre degisikliginden sonra paketi yeniden build etmeye gerek yok
(`--symlink-install` sayesinde yaml dogrudan okunur), sadece launch'i
yeniden baslatmak yeterli:

```bash
pkill -9 -f gzserver; pkill -9 -f gzclient
ros2 launch gemstone_frontier_explorer auto_mapping.launch.py \
  world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/house.world
```
