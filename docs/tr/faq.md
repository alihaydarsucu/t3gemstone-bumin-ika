# Sıkça Sorulan Sorular

## Linux zorunlu mu?

Evet. Bu sürümün ana hedefi Linux tarafında çalışmaktır.

## RTOS gerekiyor mu?

Bu sürüm için hayır. Ana hedef Linux üzerinde çalışan ROS 2 node'larıdır.

## Kamera neden ayrı yazılıyor?

Çünkü kamera hem sürücü hem işleme açısından daha farklı bir veri yoluna sahiptir ve ayrı node olarak yönetilmesi daha sağlıklıdır.

## ROS topic'leri nasıl üretiliyor?

Bu proje için hedef Linux üzerinde çalışan ROS 2 node'larıyla topic üretmektir.

## Motor neden GPIO yerine UART ile sürülüyor?

İlk taslakta (`BLUEPRINT.md`) motorların doğrudan GPIO ile sürülmesi
düşünülmüştü. Ekip, motorların harici bir sürücü karta bağlı olacağına ve bu
karta Linux'tan UART üzerinden komut gönderileceğine karar verdi
(`gemstone_motor_driver` paketi). GPIO'dan doğrudan sürme bu proje için
kullanılmıyor.

## Araç Ackermann (RC araba) tipi mi, diferansiyel sürüş mü?

Diferansiyel sürüş: 2 bağımsız tahrik tekeri + önde pasif bir misket/caster
teker. Direksiyon servosu yok; dönüş, iki tekerin hız farkıyla sağlanır.

## Neden özel ROS mesaj tipleri (`.msg`) yok?

Bilinçli bir tercih: `sensor_msgs`, `geometry_msgs`, `std_msgs`,
`diagnostic_msgs` gibi standart tipler kullanılıyor ki `teleop_twist_keyboard`,
`rqt`, Nav2, `slam_toolbox` gibi hazır araçlar ek remap/dönüşüm olmadan
doğrudan çalışsın. Detay için `interfaces/msg/README.md`.

## RPLidar için hangi ROS 2 paketi kullanılıyor?

Slamtec'in resmi `sllidar_ros2` paketi (community `rplidar_ros` fork'ları
değil).
