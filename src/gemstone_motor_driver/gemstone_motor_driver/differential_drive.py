"""Diferansiyel surus (2 tahrik tekeri + on misket teker) kinematigi.

Bu modul saf matematik icerir, ROS/seri port'a bagimli degildir; bu sayede
donanim olmadan da pytest ile test edilebilir.
"""

from dataclasses import dataclass


@dataclass
class WheelSpeeds:
    left_mps: float
    right_mps: float


def twist_to_wheel_speeds(linear_x: float, angular_z: float, wheel_separation: float) -> WheelSpeeds:
    """cmd_vel (Twist.linear.x, Twist.angular.z) degerlerini sol/sag teker
    dogrusal hizina (m/s) cevirir.

    wheel_separation: iki tahrik tekeri arasindaki mesafe (metre).
    """
    half_sep = wheel_separation / 2.0
    left = linear_x - angular_z * half_sep
    right = linear_x + angular_z * half_sep
    return WheelSpeeds(left_mps=left, right_mps=right)


def wheel_speed_to_percent(speed_mps: float, max_wheel_speed_mps: float) -> float:
    """Tekerlek dogrusal hizini (m/s) [-100, 100] araliginda bir duty-cycle
    yuzdesine olcekler ve sinirlar (clamp).
    """
    if max_wheel_speed_mps <= 0.0:
        raise ValueError('max_wheel_speed_mps pozitif olmali')
    percent = (speed_mps / max_wheel_speed_mps) * 100.0
    return max(-100.0, min(100.0, percent))
