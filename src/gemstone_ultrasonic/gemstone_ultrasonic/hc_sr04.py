"""HC-SR04 benzeri ultrasonik sensoru libgpiod ile suren/olculen sinif.

Olcum dongusu: trig pinine ~10us'lik bir HIGH darbe verilir, sensor bunun
uzerine bir ultrasonik darbe yollar ve yankiyi bekler; echo pini yankinin
gidis-donus suresi kadar HIGH kalir. Bu sure `pulse_width_to_distance` ile
mesafeye cevrilir.

NOT: Python'da `time.sleep()` mikrosaniye hassasiyeti GARANTI ETMEZ (isletim
sistemi zamanlayicisina bagli, birkaç yuz mikrosaniyeye kadar sapabilir).
HC-SR04 klonlari genelde bu toleransa izin verir (minimum ~10us, ust sinir
pratikte esnek); kesin zamanlama gerekiyorsa donanimsal PWM/timer
kullanilmasi gerekir.
"""

import time

try:
    import gpiod
except ImportError:  # pragma: no cover - sadece Linux/karti disinda (ör. gelistirme makinesi)
    gpiod = None

from gemstone_ultrasonic.ultrasonic_math import pulse_width_to_distance


class HcSr04Sensor:

    def __init__(self, chip: 'gpiod.Chip', trig_line_offset: int, echo_line_offset: int,
                 consumer: str = 'gemstone_ultrasonic', timeout_sec: float = 0.03):
        if trig_line_offset < 0 or echo_line_offset < 0:
            raise ValueError('trig_line_offset ve echo_line_offset yapilandirilmali (>= 0)')
        self._timeout_sec = timeout_sec
        self._trig = chip.get_line(trig_line_offset)
        self._echo = chip.get_line(echo_line_offset)
        self._trig.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
        self._echo.request(consumer=consumer, type=gpiod.LINE_REQ_EV_BOTH_EDGES)

    def measure_distance(self):
        """Bir olcum dongusu calistirir. Basariliysa mesafeyi (metre),
        zaman asiminda (engel yok / menzil disi / sensor bagli degil) None
        dondurur.
        """
        self._trig.set_value(1)
        time.sleep(0.00001)  # ~10us hedef, bkz. modul docstring'i
        self._trig.set_value(0)

        rising_ts = self._wait_for_edge(gpiod.LineEvent.RISING_EDGE)
        if rising_ts is None:
            return None
        falling_ts = self._wait_for_edge(gpiod.LineEvent.FALLING_EDGE)
        if falling_ts is None:
            return None

        pulse_seconds = falling_ts - rising_ts
        return pulse_width_to_distance(pulse_seconds)

    def _wait_for_edge(self, expected_type):
        if not self._echo.event_wait(sec=0, nsec=int(self._timeout_sec * 1e9)):
            return None
        event = self._echo.event_read()
        if event.type != expected_type:
            return None
        return event.sec + event.nsec / 1e9

    def release(self):
        self._trig.release()
        self._echo.release()
