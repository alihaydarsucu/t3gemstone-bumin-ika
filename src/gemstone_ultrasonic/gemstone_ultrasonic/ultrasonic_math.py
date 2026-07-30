"""HC-SR04 benzeri ultrasonik sensor icin saf mesafe hesaplama.

ROS/libgpiod'a bagimli degildir, donanim olmadan pytest ile test edilebilir.
"""

SPEED_OF_SOUND_MPS = 343.0  # ~20 derece C'de havada ses hizi


def pulse_width_to_distance(pulse_seconds: float, speed_of_sound_mps: float = SPEED_OF_SOUND_MPS) -> float:
    """Echo pininin HIGH kaldigi sureden (saniye) mesafeyi (metre) hesaplar.

    Ses dalgasi hem gidip hem donup echo'ya ulastigi icin katedilen mesafe
    (pulse_seconds * hiz) 'in yarisidir.
    """
    if pulse_seconds < 0.0:
        raise ValueError('pulse_seconds negatif olamaz')
    return (pulse_seconds * speed_of_sound_mps) / 2.0
