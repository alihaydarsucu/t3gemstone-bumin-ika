"""Lidar taramasindan on koni icindeki en yakin engeli hesaplayan ve buna
gore hiz komutunu sinirlayan saf fonksiyonlar. ROS'a bagimli degildir,
donanim olmadan pytest ile test edilebilir.
"""

import math
from dataclasses import dataclass


@dataclass
class TwistLimitResult:
    linear_x: float
    angular_z: float
    blocked: bool


def compute_min_forward_distance(
    ranges,
    angle_min: float,
    angle_increment: float,
    range_min: float,
    range_max: float,
    forward_half_angle_rad: float,
    forward_angle_offset_rad: float = 0.0,
) -> float:
    """`ranges` (LaserScan.ranges) icinde, aracin tam onunu (0 rad, mount
    yonelimine gore forward_angle_offset_rad ile duzeltilebilir) merkez alan
    +-forward_half_angle_rad'lik koni icindeki gecerli en kucuk mesafeyi
    dondurur. Hicbir gecerli olcum yoksa math.inf doner (engel yok demektir).
    """
    min_distance = math.inf
    for i, r in enumerate(ranges):
        if not math.isfinite(r):
            continue
        if r < range_min or r > range_max:
            continue
        angle = angle_min + i * angle_increment - forward_angle_offset_rad
        angle = math.atan2(math.sin(angle), math.cos(angle))  # [-pi, pi] araligina normalize et
        if abs(angle) <= forward_half_angle_rad:
            min_distance = min(min_distance, r)
    return min_distance


def limit_twist(linear_x: float, angular_z: float, min_forward_distance: float,
                 safety_distance: float) -> TwistLimitResult:
    """Sadece ileri harekette (linear_x > 0) ve on konide engel esigin
    altindayken ileri hizi sifirlar. Geri gitmeye veya yerinde donmeye
    (linear_x <= 0) mudahale etmez -- engelden uzaklasmayi engellememek icin.
    """
    if linear_x > 0.0 and min_forward_distance < safety_distance:
        return TwistLimitResult(linear_x=0.0, angular_z=angular_z, blocked=True)
    return TwistLimitResult(linear_x=linear_x, angular_z=angular_z, blocked=False)
