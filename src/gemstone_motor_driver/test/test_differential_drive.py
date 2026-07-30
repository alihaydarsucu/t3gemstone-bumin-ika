import math

import pytest

from gemstone_motor_driver.differential_drive import (
    twist_to_wheel_speeds,
    wheel_speed_to_percent,
    wheel_speeds_to_twist,
    ticks_to_distance,
    OdometryIntegrator,
)


def test_straight_line_gives_equal_wheel_speeds():
    speeds = twist_to_wheel_speeds(linear_x=1.0, angular_z=0.0, wheel_separation=0.3)
    assert speeds.left_mps == pytest.approx(1.0)
    assert speeds.right_mps == pytest.approx(1.0)


def test_pure_rotation_gives_opposite_wheel_speeds():
    speeds = twist_to_wheel_speeds(linear_x=0.0, angular_z=1.0, wheel_separation=0.3)
    assert speeds.left_mps == pytest.approx(-0.15)
    assert speeds.right_mps == pytest.approx(0.15)


def test_wheel_speed_to_percent_clamps_range():
    assert wheel_speed_to_percent(2.0, max_wheel_speed_mps=1.0) == 100.0
    assert wheel_speed_to_percent(-2.0, max_wheel_speed_mps=1.0) == -100.0
    assert wheel_speed_to_percent(0.5, max_wheel_speed_mps=1.0) == pytest.approx(50.0)


def test_wheel_speed_to_percent_rejects_non_positive_max():
    with pytest.raises(ValueError):
        wheel_speed_to_percent(0.5, max_wheel_speed_mps=0.0)


def test_wheel_speeds_to_twist_is_inverse_of_twist_to_wheel_speeds():
    speeds = twist_to_wheel_speeds(linear_x=0.5, angular_z=0.8, wheel_separation=0.3)
    twist = wheel_speeds_to_twist(speeds.left_mps, speeds.right_mps, wheel_separation=0.3)
    assert twist.linear_x == pytest.approx(0.5)
    assert twist.angular_z == pytest.approx(0.8)


def test_wheel_speeds_to_twist_rejects_non_positive_separation():
    with pytest.raises(ValueError):
        wheel_speeds_to_twist(1.0, 1.0, wheel_separation=0.0)


def test_ticks_to_distance_one_full_revolution():
    distance = ticks_to_distance(ticks=20, ticks_per_revolution=20.0, wheel_radius=0.033)
    assert distance == pytest.approx(2.0 * math.pi * 0.033)


def test_ticks_to_distance_negative_ticks_gives_negative_distance():
    distance = ticks_to_distance(ticks=-10, ticks_per_revolution=20.0, wheel_radius=0.033)
    assert distance < 0.0


def test_ticks_to_distance_rejects_non_positive_ticks_per_revolution():
    with pytest.raises(ValueError):
        ticks_to_distance(ticks=10, ticks_per_revolution=0.0, wheel_radius=0.033)


def test_odometry_integrator_straight_line():
    integrator = OdometryIntegrator()
    pose = integrator.update(linear_x=1.0, angular_z=0.0, dt=1.0)
    assert pose.x == pytest.approx(1.0)
    assert pose.y == pytest.approx(0.0)
    assert pose.theta == pytest.approx(0.0)


def test_odometry_integrator_accumulates_across_updates():
    integrator = OdometryIntegrator()
    integrator.update(linear_x=1.0, angular_z=0.0, dt=1.0)
    pose = integrator.update(linear_x=1.0, angular_z=0.0, dt=1.0)
    assert pose.x == pytest.approx(2.0)


def test_odometry_integrator_pure_rotation_does_not_translate():
    integrator = OdometryIntegrator()
    pose = integrator.update(linear_x=0.0, angular_z=math.pi / 2.0, dt=1.0)
    assert pose.x == pytest.approx(0.0, abs=1e-9)
    assert pose.y == pytest.approx(0.0, abs=1e-9)
    assert pose.theta == pytest.approx(math.pi / 2.0)


def test_odometry_integrator_ignores_non_positive_dt():
    integrator = OdometryIntegrator()
    pose = integrator.update(linear_x=1.0, angular_z=0.0, dt=0.0)
    assert pose.x == pytest.approx(0.0)
