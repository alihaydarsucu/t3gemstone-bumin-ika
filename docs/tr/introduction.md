# Tanıtım

## T3 Gemstone Linux ROS Bringup

Bu proje, T3 Gemstone O1 kartı üzerinde **tamamen Linux tarafında çalışan** bir
robotik bringup katmanı kurmak için hazırlanmıştır. Hedef araç: diferansiyel
sürüşlü (2 tahrik teker + ön misket teker) bir insansız kara aracı (İKA).
Hedef, OpenCR benzeri "açılışta otomatik topic yayını" davranışını Gemstone'un Linux mimarisine uyarlamaktır.

## Neden Bu Proje?

Gemstone güçlü bir gömülü bilgisayar mimarisi sunar.
Bu proje, o yapıyı tek karttan çalışabilen bir ROS 2 yayın ve kontrol merkezine dönüştürmeyi amaçlar.

Öncelikler:

1. Linux üzerinde çalışan ROS 2 node'ları
2. Açılışta otomatik çalışan bringup servisleri
3. Net topic isimleri ve veri akışı
4. Kamera, lidar ve motor için örnek uygulamalar

## Kapsam

- Gemstone sensörleri
- Harici `A1M8` RPLidar
- Kamera sürücüsü
- Kamera görüntü işleme örneği
- Harici motor sürücüsü
- Linux tabanlı bringup

## Kısa Hedef

Kart açıldığında sensörler ve eyleyiciler çalışsın, topic'ler üretilebilsin ve sistem robot kontrolüne hazır hale gelsin.
