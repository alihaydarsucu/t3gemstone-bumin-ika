import math

import pytest

from gemstone_motor_driver.motion_state import (
    accel_to_roll_pitch,
    average_angles,
    wrap_angle,
)


def test_wrap_angle_keeps_value_in_range():
    wrapped = wrap_angle(4.0 * math.pi)
    assert wrapped == pytest.approx(0.0)


def test_wrap_angle_handles_negative_overflow():
    wrapped = wrap_angle(-1.5 * math.pi)
    assert wrapped == pytest.approx(math.pi / 2.0)


def test_average_angles_blends_across_pi_boundary():
    blended = average_angles(math.radians(179.0), math.radians(-179.0), primary_weight=0.5)
    assert abs(abs(blended) - math.pi) < math.radians(2.0)


def test_average_angles_rejects_invalid_weight():
    with pytest.raises(ValueError):
        average_angles(0.0, 0.0, primary_weight=1.2)


def test_accel_to_roll_pitch_on_upright_gravity_vector():
    roll, pitch = accel_to_roll_pitch(0.0, 0.0, 9.81)
    assert roll == pytest.approx(0.0)
    assert pitch == pytest.approx(0.0)


def test_accel_to_roll_pitch_returns_zero_for_zero_vector():
    roll, pitch = accel_to_roll_pitch(0.0, 0.0, 0.0)
    assert roll == pytest.approx(0.0)
    assert pitch == pytest.approx(0.0)
