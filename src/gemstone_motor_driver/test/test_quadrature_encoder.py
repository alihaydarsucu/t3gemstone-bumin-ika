from gemstone_motor_driver.quadrature_encoder import decode_tick_direction


def test_decode_tick_direction_forward_when_b_low():
    assert decode_tick_direction(channel_b_level=0) == 1


def test_decode_tick_direction_backward_when_b_high():
    assert decode_tick_direction(channel_b_level=1) == -1


def test_decode_tick_direction_invert_flips_sign():
    assert decode_tick_direction(channel_b_level=0, invert=True) == -1
    assert decode_tick_direction(channel_b_level=1, invert=True) == 1
