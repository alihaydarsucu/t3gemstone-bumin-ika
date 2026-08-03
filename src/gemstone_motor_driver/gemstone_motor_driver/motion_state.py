"""IMU + wheel odom tabanli hareket durumu yardimci fonksiyonlari.

Bu modul ROS bagimli olmayan kucuk matematik parcalarini bir arada tutar.
Boylece aci sarmalama ve sensör birlestirme mantigi pytest ile test edilebilir.
"""

import math


def wrap_angle(angle: float) -> float:
    """Aciyi [-pi, pi) araligina sarar."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def average_angles(primary: float, secondary: float, primary_weight: float = 0.7) -> float:
    """Iki aciyi sarmali ortalama ile birlestirir.

    `primary_weight` 0 ile 1 arasinda olmalidir; deger buyudukce primary
    aci daha baskin olur.
    """
    if not 0.0 <= primary_weight <= 1.0:
        raise ValueError('primary_weight 0.0 ile 1.0 arasinda olmali')
    x = math.cos(primary) * primary_weight + math.cos(secondary) * (1.0 - primary_weight)
    y = math.sin(primary) * primary_weight + math.sin(secondary) * (1.0 - primary_weight)
    if x == 0.0 and y == 0.0:
        return wrap_angle(primary)
    return wrap_angle(math.atan2(y, x))


def accel_to_roll_pitch(ax: float, ay: float, az: float) -> tuple[float, float]:
    """Ivmelenme vektorunden yaklasik roll/pitch hesaplar.

    IMU orientasyonu yoksa veya kapaliyken robotun egim bilgisini korumak icin
    kullanilir. Vektor sifirsa guvenli olarak (0, 0) dondurur.
    """
    norm = math.sqrt(ax * ax + ay * ay + az * az)
    if norm <= 0.0:
        return 0.0, 0.0

    ax /= norm
    ay /= norm
    az /= norm

    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))
    return roll, pitch

