import pytest

from gemstone_ultrasonic.ultrasonic_math import pulse_width_to_distance, SPEED_OF_SOUND_MPS


def test_pulse_width_to_distance_known_value():
    # 1 metredeki bir engel icin gidis-donus suresi ~ 2*1/343 s.
    pulse_seconds = 2.0 * 1.0 / SPEED_OF_SOUND_MPS
    assert pulse_width_to_distance(pulse_seconds) == pytest.approx(1.0)


def test_pulse_width_to_distance_zero_pulse_is_zero_distance():
    assert pulse_width_to_distance(0.0) == 0.0


def test_pulse_width_to_distance_rejects_negative_pulse():
    with pytest.raises(ValueError):
        pulse_width_to_distance(-0.001)


def test_pulse_width_to_distance_respects_custom_speed_of_sound():
    distance = pulse_width_to_distance(1.0, speed_of_sound_mps=100.0)
    assert distance == pytest.approx(50.0)
