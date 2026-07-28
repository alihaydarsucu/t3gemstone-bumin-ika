import pytest

from gemstone_motor_driver.differential_drive import (
    twist_to_wheel_speeds,
    wheel_speed_to_percent,
)
from gemstone_motor_driver.protocol import encode_speed_command, encode_stop_command


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


def test_encode_speed_command_format():
    assert encode_speed_command(50, -50) == b'$M,50,-50\n'


def test_encode_stop_command_is_zero():
    assert encode_stop_command() == b'$M,0,0\n'
