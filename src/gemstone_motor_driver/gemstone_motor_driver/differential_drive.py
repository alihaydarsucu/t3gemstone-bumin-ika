"""Diferansiyel surus (2 tahrik tekeri + on misket teker) kinematigi.

Bu modul saf matematik icerir, ROS/seri port'a bagimli degildir; bu sayede
donanim olmadan da pytest ile test edilebilir.
"""

import math
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


@dataclass
class Twist2D:
    linear_x: float
    angular_z: float


def wheel_speeds_to_twist(left_mps: float, right_mps: float, wheel_separation: float) -> Twist2D:
    """twist_to_wheel_speeds'in tersi: enkoderden olculen sol/sag teker
    dogrusal hizlarindan (m/s) robotun linear_x/angular_z hizini cikarir.
    Odometri hesaplamak icin kullanilir.
    """
    if wheel_separation <= 0.0:
        raise ValueError('wheel_separation pozitif olmali')
    linear_x = (left_mps + right_mps) / 2.0
    angular_z = (right_mps - left_mps) / wheel_separation
    return Twist2D(linear_x=linear_x, angular_z=angular_z)


def ticks_to_distance(ticks: int, ticks_per_revolution: float, wheel_radius: float) -> float:
    """Enkoder tik sayisini tekerlegin kat ettigi mesafeye (metre) cevirir."""
    if ticks_per_revolution <= 0.0:
        raise ValueError('ticks_per_revolution pozitif olmali')
    revolutions = ticks / ticks_per_revolution
    return revolutions * 2.0 * math.pi * wheel_radius


@dataclass
class Pose2D:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class OdometryIntegrator:
    """Diferansiyel surus icin basit "dead reckoning" pozisyon takipcisi.

    Her adimda (dt saniye boyunca) olculen linear_x/angular_z hizini
    entegre ederek x, y, theta konumunu gunceller. Kayma (wheel slip) veya
    IMU/lidar duzeltmesi icermez -- sadece tekerlek odometrisidir.
    """

    def __init__(self):
        self.pose = Pose2D()

    def update(self, linear_x: float, angular_z: float, dt: float) -> Pose2D:
        if dt <= 0.0:
            return self.pose
        delta_theta = angular_z * dt
        # Yari-adim (midpoint) entegrasyonu: kisa dt'lerde duz-cizgi
        # yaklastirmasindan biraz daha dogru, ekstra maliyeti yok.
        mid_theta = self.pose.theta + delta_theta / 2.0
        self.pose.x += linear_x * math.cos(mid_theta) * dt
        self.pose.y += linear_x * math.sin(mid_theta) * dt
        self.pose.theta += delta_theta
        return self.pose
