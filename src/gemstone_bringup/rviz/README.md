# RViz konfigurasyonu

Henuz kayitli bir `.rviz` konfigurasyon dosyasi yok. Karta baglanip
`bringup.launch.py enable_rviz:=true` ile RViz'i actiktan sonra
TF/LaserScan/Image/Odometry displaylerini elle ekleyip
`File > Save Config As` ile bu klasore `gemstone_ugv.rviz` olarak
kaydedin; bir sonraki acilista launch dosyasina
`rviz_config:=<yol>` argumaniyla bu dosyayi verecek sekilde
`bringup.launch.py` kucuk bir guncelleme ile genisletilebilir.
