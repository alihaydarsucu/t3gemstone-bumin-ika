# Mimari

## Genel Akış

```
Sensörler / Lidar / Kamera / Motor
        │
        ▼
A53 / Linux Katmanı
        ├── ROS 2 driver node'ları
        ├── launch orkestrasyonu
        ├── diagnostics / health
        └── kayıt / debug / işleme
```

## Katmanlar

### Linux / A53
- board init
- driver init
- topic publish
- watchdog
- motor safety
- kamera işleme örneği
- logging / visualization

## Mimari Kural

Bu projede sensör verisi ve ROS topic'leri mümkün olduğunca Linux tarafında üretilir.
RTOS yaklaşımı bu sürümün kapsamı dışındadır.

## Tasarım Sonucu

Bu yaklaşım sayesinde:

- açılış daha sade olur
- kontrol akışı tek yerde toplanır
- sensör ve motor akışı tek launch altında yönetilir
- kamera gibi ağır işler ayrı node'lara bölünebilir
