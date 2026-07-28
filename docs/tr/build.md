# Kurulum ve Build

Bu repo Linux-first bir ROS 2 çalışma alanı olarak hazırlanır.

## Beklenen Yerleşim

- `src/gemstone_bringup/` - ROS 2 paket kodu
- `docs/` - proje notları
- `hardware/` - bağlantı bilgileri
- `tools/` - yardımcı betikler

## Build Mantığı

ROS 2 kurulu bir sistemde tipik akış:

1. workspace kökünde `colcon build`
2. ortamı `source install/setup.bash` ile yükleme
3. `ros2 launch gemstone_bringup bringup.launch.py` ile çalıştırma

## Container Yolu

Bu repo içinde bir `Dockerfile` bulunur.
Bu yol, ROS 2 Humble kurulumu olmayan ya da yerel binary paketleri için uygun olmayan sistemlerde daha güvenli bir test ortamı sağlar.

Önerilen akış:

1. `docker build -t gemstone-bringup-humble .`
2. `docker run -it --rm -v "$PWD:/workspace" gemstone-bringup-humble`
3. container içinde `source /opt/ros/humble/setup.bash`
4. ardından `colcon build`

## Not

Bu proje için hedef, tüm ana iş akışını Linux üzerinde çalıştırmaktır.
