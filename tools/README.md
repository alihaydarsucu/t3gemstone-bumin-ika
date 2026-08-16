# Araçlar

Bu klasör kısa yardımcı notlar içindir. Uzun kullanım rehberleri docs reposuna taşındı.

> **[TR]** Yardımcı araçların kısa notları burada kalır.
>
> **[EN]** Short notes for helper tools stay here.

## Hızlı Bağlantı

- [Türkçe dokümantasyon](https://docs.t3gemstone.org/tr/build)
- [English documentation](https://docs.t3gemstone.org/en/build)

## GCS Başlatma (gcs.sh)

Host'tan tek komutla konteyneri başlatıp tarayıcı GCS'sini açar
(`docker exec` yapıştırma yarışını önler):

```bash
./tools/gcs.sh                          # office.world
./tools/gcs.sh house                    # ev dünyası (house.world)
./tools/gcs.sh world_file:=/path/to/world.world   # özel dünya
```

Launch yüklendikten sonra tarayıcıda **http://localhost:8000** açılır.
Ayrıntılar: [docs/tr/gcs.md](../docs/tr/gcs.md).

## Planlanan Araçlar

- build sarmalayıcı
- cihaz varlık kontrolü
- log toplama
- imaj yazma yardımcısı
