"""Basit (naive) engelden kacinma karar mantigi.

https://github.com/enansakib/obstacle-avoidance-turtlebot reposundaki
`naive_obs_avoid_tb3.py` algoritmasinin ROS 2 + Python 3'e tasinmis,
donanimdan bagimsiz cekirdegi: on ve on-sol/on-sag mesafelerine esik
karsilastirmasi yapip git/don karari verir.

Bu, `gemstone_exploration_demo`'daki durum makineli (SELECT_GOAL/SEEK_GOAL/
WALL_FOLLOW/RECOVER) algoritmanin yerini almaz -- onun yaninda, daha basit
ve ogretici bir alternatif olarak sunuluyor.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NaiveAvoidanceCommand:
    linear_x: float
    angular_z: float


def decide_naive_avoidance(
    front_distance: float,
    left_distance: float,
    right_distance: float,
    distance_threshold: float,
    forward_speed: float,
    turn_speed: float,
) -> NaiveAvoidanceCommand:
    """Onde ve on-sol/on-sag'da mesafe esigin uzerindeyse ileri gider,
    degilse durup sabit yonde doner -- orijinal algoritmadaki iki durumlu
    (git / don) davranisin birebir karsiligi.
    """
    path_clear = (
        front_distance > distance_threshold
        and left_distance > distance_threshold
        and right_distance > distance_threshold
    )
    if path_clear:
        return NaiveAvoidanceCommand(linear_x=forward_speed, angular_z=0.0)
    return NaiveAvoidanceCommand(linear_x=0.0, angular_z=turn_speed)
