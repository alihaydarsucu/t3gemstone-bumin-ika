import math

import pytest

from gemstone_obstacle_avoidance.lidar_safety import (
    compute_min_forward_distance,
    limit_twist,
)


def test_compute_min_forward_distance_finds_closest_in_cone():
    # 5 olcum, -90..+90 derece arasi, 45 derece adimlarla.
    ranges = [5.0, 3.0, 1.0, 3.0, 5.0]
    dist = compute_min_forward_distance(
        ranges=ranges,
        angle_min=math.radians(-90),
        angle_increment=math.radians(45),
        range_min=0.1,
        range_max=10.0,
        forward_half_angle_rad=math.radians(30),
    )
    # Sadece tam onde (index 2, 1.0 m) koni icinde kalir.
    assert dist == pytest.approx(1.0)


def test_compute_min_forward_distance_ignores_invalid_readings():
    ranges = [math.inf, math.nan, 0.0, 20.0]
    dist = compute_min_forward_distance(
        ranges=ranges,
        angle_min=0.0,
        angle_increment=0.0,
        range_min=0.1,
        range_max=10.0,
        forward_half_angle_rad=math.pi,
    )
    assert dist == math.inf


def test_compute_min_forward_distance_respects_angle_offset():
    # Ham acilar: index0=0 derece (1.0m), index1=90 derece (5.0m).
    ranges = [1.0, 5.0, 5.0, 5.0]
    # Offsetsiz: 0 derece (ham) = arac onu sayilir -> index0 koni icinde.
    dist_no_offset = compute_min_forward_distance(
        ranges=ranges, angle_min=0.0, angle_increment=math.radians(90),
        range_min=0.1, range_max=10.0, forward_half_angle_rad=math.radians(30))
    # Sensor gercekte 90 derece donuk monte edilmis: arac onu ham 90
    # derecede. Offset=90 derece ile duzeltince index1 koni icine girmeli,
    # index0 (ham 0 derece -> duzeltilmis -90 derece) disina dusmeli.
    dist_with_offset = compute_min_forward_distance(
        ranges=ranges, angle_min=0.0, angle_increment=math.radians(90),
        range_min=0.1, range_max=10.0, forward_half_angle_rad=math.radians(30),
        forward_angle_offset_rad=math.radians(90))
    assert dist_no_offset == pytest.approx(1.0)
    assert dist_with_offset == pytest.approx(5.0)


def test_limit_twist_blocks_forward_motion_when_close():
    result = limit_twist(linear_x=0.5, angular_z=0.1, min_forward_distance=0.2, safety_distance=0.4)
    assert result.linear_x == 0.0
    assert result.angular_z == pytest.approx(0.1)
    assert result.blocked is True


def test_limit_twist_allows_reverse_even_when_close():
    result = limit_twist(linear_x=-0.5, angular_z=0.0, min_forward_distance=0.1, safety_distance=0.4)
    assert result.linear_x == pytest.approx(-0.5)
    assert result.blocked is False


def test_limit_twist_passes_through_when_clear():
    result = limit_twist(linear_x=0.5, angular_z=0.2, min_forward_distance=2.0, safety_distance=0.4)
    assert result.linear_x == pytest.approx(0.5)
    assert result.blocked is False
