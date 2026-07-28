# Kamera Görüntü İşleme Örneği

Bu örneğin gerçek implementasyonu artık `src/gemstone_image_proc` paketinde
yaşıyor (`image_processing_node.py`). Bu klasör, önceki taslakta ayrılmış bir
yer tutucuydu; kod yazıldıktan sonra gerçek pakete taşındı.

## Ne Yapıyor (bugün)

- `camera/image_raw`'i dinler, `cv_bridge` ile OpenCV formatına çevirir
- `process_frame()` içinde şu an passthrough (frame'i değiştirmeden geçirir)
- `camera/image_processed`'e yeniden yayınlar

## Sonraki Adım

Gerçek görev (şerit takibi, engel/renk tespiti vb.) netleşince
`process_frame()` fonksiyonu doldurulacak. Detay için
[../../docs/tr/camera.md](../../docs/tr/camera.md).
