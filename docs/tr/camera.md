# Kamera

## Hedef

Kamera için iki parça tanımlanır:

1. kamera sürücüsü
2. örnek görüntü işleme node'u

## Sorumluluk Ayrımı

### Sürücü
- sensörü başlatır
- kare veya satır verisini toplar
- ham akışı çıkarır

### İşleme Node'u
- temel filtreleme
- görüntü ön işleme
- örnek nesne / kenar / renk işleme
- çıktı üretimi

## Çalışma Yeri

- sürücü katmanı Linux üzerinde
- ağır işlem gerekirse ayrı bir görüntü işleme node'u

## Örnek Kullanım

- kamera bağlandı
- sürücü açıldı
- ham frame alındı
- örnek işleme node'u çalıştı
- çıktı topic'i üretildi

## Not

Bu bölüm, daha sonra gerçek sensör ve arayüz netleşince detaylandırılır.
