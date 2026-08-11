<p align="center">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/t3gemstone/docs/main/logo/dark.png" width="40%" />
        <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/t3gemstone/docs/main/logo/light.png" width="40%" />
        <img alt="T3 Foundation" src="https://raw.githubusercontent.com/t3gemstone/docs/main/logo/light.png" width="40%" />
    </picture>
</p>

# T3 Gemstone Bumin IKA

<p align="center">
  <a href="https://t3gemstone.org"><img alt="T3 Foundation" src="https://raw.githubusercontent.com/t3gemstone/docs/main/images/t3-foundation.svg"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img alt="License" src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"></a>
  <a href="https://github.com/alitalhq/t3gemstone-bumin-ika-docs"><img alt="Docs repo" src="https://img.shields.io/badge/Docs-repo-red.svg"></a>
  <a href="https://github.com/alitalhq/t3gemstone-bumin-ika-docs/tree/main/docs/tr/01-kart-kurulumu.md"><img alt="TR docs" src="https://img.shields.io/badge/Docs-TR-red.svg"></a>
  <a href="https://github.com/alitalhq/t3gemstone-bumin-ika-docs/tree/main/docs/en/01-board-setup.md"><img alt="EN docs" src="https://img.shields.io/badge/Docs-EN-blue.svg"></a>
</p>

> **[TR]** T3 Gemstone O1 üzerinde çalışan, sensörler ve motor akışlarını tek bir ROS 2 bringup hattında toplayan diferansiyel sürüşlü İKA projesi.
>
> **[EN]** A differential-drive UGV project running on the T3 Gemstone O1, bringing sensors and motor workflows together in a single ROS 2 bringup flow.

<p align="center">
  <img src="assets/ugv-bare-chassis.jpeg" alt="Bare chassis" width="31%" />
  <img src="assets/ugv-wiring-rear.jpeg" alt="Wiring rear view" width="31%" />
  <img src="assets/ugv-assembled-front.jpeg" alt="Assembled front view" width="31%" />
</p>

## Kısa Tanım

Bu repo ana uygulama kodunu ve kısa çalışma notlarını içerir. Ayrıntılı dokümantasyon için doğrudan kaynak dosyalara geçin:

- [Türkçe dokümanlar](https://github.com/alitalhq/t3gemstone-bumin-ika-docs/tree/main/docs/tr)
- [English docs](https://github.com/alitalhq/t3gemstone-bumin-ika-docs/tree/main/docs/en)
- [Docs repo README](https://github.com/alitalhq/t3gemstone-bumin-ika-docs/blob/main/README.md)

Tek kart yaklaşımı kullanılır. IMU, motor sürücü, ultrasonik sensörler, lidar ve kamera Linux tarafındaki ROS 2 node'ları ile çalışır.

## Neler Var?

- `src/` - ROS 2 paketleri
- `hardware/` - kısa donanım notları
- `tools/` - yardımcı araçlar için kısa alan
- `docs/llms.txt` - docs reposundaki içerik haritası

## Durum

| Alan | Durum |
|---|---|
| Bringup | Tek launch ile çalışıyor |
| Dokümantasyon | Ayrıntılı içerik docs reposunda |
| Dil desteği | TR / EN girişleri mevcut |

## Devam

- [Dokümantasyon Girişi](https://github.com/alitalhq/t3gemstone-bumin-ika-docs/tree/main/docs/tr/01-kart-kurulumu.md)
- [English Documentation](https://github.com/alitalhq/t3gemstone-bumin-ika-docs/tree/main/docs/en/01-board-setup.md)
