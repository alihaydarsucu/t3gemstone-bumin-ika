"""Harici motor surucu kart ile UART uzerinden konusulan cerceve (frame)
formati.

ONEMLI: Bu, gercek surucu kartin protokolu netlesene kadar kullanilacak bir
YER TUTUCUDUR (placeholder). Format: ASCII, insan tarafindan okunabilir,
tek satir, "$M,<sol_yuzde>,<sag_yuzde>\\n". Yuzdeler -100..100 araliginda
tam sayidir (-100 = tam geri, 100 = tam ileri, 0 = dur).

Gercek kart protokolu belli oldugunda sadece bu dosyayi degistirmeniz
yeterli olmali; motor_driver_node.py bu modulun disina bagimli degildir.
"""

FRAME_PREFIX = '$M'


def encode_speed_command(left_percent: float, right_percent: float) -> bytes:
    left = max(-100, min(100, round(left_percent)))
    right = max(-100, min(100, round(right_percent)))
    frame = f'{FRAME_PREFIX},{left},{right}\n'
    return frame.encode('ascii')


def encode_stop_command() -> bytes:
    return encode_speed_command(0, 0)
