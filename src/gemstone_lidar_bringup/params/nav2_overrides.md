# Nav2 parametreleri hakkinda not

Tam bir `nav2_params.yaml` (300+ satir, costmap katmanlari, controller/planner
plugin ayarlari vb.) elle sifirdan yazip repoya koymak yerine, Nav2'nin kendi
`nav2_bringup` paketiyle gelen varsayilan `params/nav2_params.yaml` dosyasini
baz almanizi oneriyoruz -- o dosya zaten test edilmis ve guncel tutuluyor;
elle yeniden yazmak ince hatalara (yanlis plugin adi, eksik alan vb.) acik.

## Yapmaniz gereken

1. `ros2 pkg prefix nav2_bringup` ile paketin kurulu yerini bulun, altindaki
   `share/nav2_bringup/params/nav2_params.yaml` dosyasini bu klasore
   (`gemstone_lidar_bringup/params/nav2_params.yaml`) kopyalayin.
2. Bu projeye ozel degistirmeniz gereken alanlar:
   - `robot_radius`: aracinizin gercek yaricapi (metre) -- costmap'lerde
     (`local_costmap` ve `global_costmap` altinda, `inflation_layer` ve
     `obstacle_layer`/`static_layer` civarinda).
   - `controller_server` altinda `max_vel_x`, `max_vel_theta`,
     `min_vel_x`, `acc_lim_x`: `gemstone_motor_driver`'daki
     `max_wheel_speed` parametresiyle tutarli olmali.
   - `robot_base_frame: base_link`, `odom_topic: /odom_rf2o` (rf2o'nun
     yayinladigi topic ile eslesmeli, bkz. lidar_bringup.launch.py).
   - Diferansiyel surus oldugumuz icin controller plugin olarak
     `DWB` (varsayilan) veya `RegulatedPurePursuit` kullanilabilir; Ackermann'a
     ozel plugin gerekmiyor.
3. `enable_nav2:=true` ile launch ederken
   `params_file:=<bu_dosyanin_tam_yolu>` argumanini gecin (bkz.
   `lidar_bringup.launch.py`).

Bu adimi siz (veya ben, karta baglanip `nav2_bringup`in kurulu oldugu
ortamda) birlikte yapabiliriz -- simdilik launch dosyasi bu params_file'i
bir launch argumanindan okuyacak sekilde hazir, sadece dosyanin kendisi
eksik.
