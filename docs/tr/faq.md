# Sıkça Sorulan Sorular

## Linux zorunlu mu?

Evet. Bu sürümün ana hedefi Linux tarafında çalışmaktır.

## RTOS gerekiyor mu?

Bu sürüm için hayır. Ana hedef Linux üzerinde çalışan ROS 2 node'larıdır.

## Kamera neden ayrı yazılıyor?

Çünkü kamera hem sürücü hem işleme açısından daha farklı bir veri yoluna sahiptir ve ayrı node olarak yönetilmesi daha sağlıklıdır.

## ROS topic'leri nasıl üretiliyor?

Bu proje için hedef Linux üzerinde çalışan ROS 2 node'larıyla topic üretmektir.

## Motorlar GPIO ile mi, UART ile mi sürülüyor?

GPIO (libgpiod), doğrudan. Projenin ilk taslağında UART ile harici bir
sürücü karta komut gönderme fikri değerlendirilmişti, ama gerçek donanım
(Harezmi robotunun motor+enkoder kartı, üzerinde bir Deneyap Kart +
MX1508 H-bridge) incelenince karar değişti: Deneyap sökülüp yerine
Gemstone'un GPIO'ları doğrudan bağlanıyor, motor yönü ve kadratür
enkoderler `gemstone_motor_driver` paketinden libgpiod ile
sürülüyor/okunuyor. Güç hâlâ harici bir 2S pilden geliyor; Gemstone sadece
kartın lojik tarafını (3.3V + GND) besliyor.

## Motorlarda değişken hız (PWM) kontrolü var mı?

Henüz yok — `gemstone_motor_driver` şu an sadece yön kontrolü yapıyor
(bang-bang: tam hız ileri/geri/dur). libgpiod salt dijital GPIO'dur, PWM
üretmez; gerçek hız kontrolü için Gemstone'un donanımsal PWM çıkışının
hangi fiziksel pinlerde olduğu netleşmeli (bkz. `BLUEPRINT.md` yol
haritası v0.4).

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
