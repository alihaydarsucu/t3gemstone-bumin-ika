# Kamera

## Karar

T3 Gemstone O1'in CSI arayüzü (IMX219/OV5640 destekli) kullanılıyor; USB
webcam veya derinlik kamerası tercih edilmedi. Kamera için iki parça var:

1. `gemstone_camera` — sürücü (launch dosyası, `v4l2_camera_node` sarmalayıcı)
2. `gemstone_image_proc` — örnek/iskelet görüntü işleme node'u

## Sorumluluk Ayrımı

### Sürücü (`gemstone_camera`)
- CSI overlay + `gem-camera-setup` sonrası oluşan `/dev/videoX`'i açar
- `v4l2_camera_node` ile ham kareyi `camera/image_raw` (`sensor_msgs/Image`)
  olarak yayınlar

### İşleme Node'u (`gemstone_image_proc`)
- şu an passthrough (frame'i işlemeden `camera/image_processed`'e yeniden yayınlar)
- `process_frame()` fonksiyonu, gerçek görev (şerit takibi, engel/renk tespiti
  vb.) netleşince doldurulmak üzere hazır; OpenCV/cv_bridge dönüşümü zaten var

## Çalışma Yeri

- sürücü katmanı Linux üzerinde (CSI + v4l2)
- işleme ayrı bir node'da (`gemstone_image_proc`), ağır CV görevleri buraya eklenir

## Kurulum Notu

Kart tarafında önce
[docs.t3gemstone.org/tr/boards/o1/peripherals/camera](https://docs.t3gemstone.org/tr/boards/o1/peripherals/camera)
adımları (device tree overlay + `gem-camera-setup`) tamamlanmalı, `/dev/videoX`
görüntü vermeye hazır olmalı.

## Not

Görüntü işleme görevi (şerit takibi mi, nesne tespiti mi, vb.) henüz
belirlenmedi; `gemstone_image_proc/image_processing_node.py` bu karara göre
genişletilecek.
