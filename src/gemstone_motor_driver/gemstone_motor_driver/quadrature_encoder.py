"""Enkoder tik sayimi: Kanal A (interrupt) kenar olayinda Kanal B'nin
seviyesine bakarak yon belirleyen basit kadratur cozucu.

Harezmi/Deneyap pin haritasinda enkoderlerin sadece Kanal A'si "interrupt"
olarak isaretliydi (bkz. proje notlari), Kanal B duz dijital giris. Bu
yuzden burada tam 4x kadratur (hem A hem B kenarlarini sayan) yerine daha
basit, tek kenarli (1x) bir cozum kullaniliyor -- donanimla tutarli ve
yeterince hassas.
"""

import threading

try:
    import gpiod
except ImportError:  # pragma: no cover - sadece Linux/karti disinda (ör. gelistirme makinesi)
    gpiod = None


def decode_tick_direction(channel_b_level: int, invert: bool = False) -> int:
    """Kanal A'da yukselen kenar olustugunda, o anki Kanal B seviyesinden
    yon isaretini (+1 ileri, -1 geri) cikarir. Bu, ROS/libgpiod'a bagimli
    olmayan saf mantik -- donanim olmadan pytest ile test edilebilir.

    Kablolamaya gore B ile yon iliskisi ters olabilir: motoru elle ileri
    dondurup tik sayacinin arttigini dogrulayin; azaliyorsa invert=True
    yapin (ROS parametresi olarak disariya acilir).
    """
    direction = 1 if channel_b_level == 0 else -1
    return -direction if invert else direction


class QuadratureEncoder:
    """libgpiod uzerinden Kanal A'nin kenar olaylarini ayri bir thread'de
    dinleyip tik sayacini gunceller. `read_and_reset_ticks()` ile ana
    (ROS) thread'den guvenli (lock'lu) sekilde okunur.
    """

    def __init__(self, chip: 'gpiod.Chip', channel_a_offset: int, channel_b_offset: int,
                 consumer: str = 'gemstone_motor_driver', invert: bool = False):
        if channel_a_offset < 0 or channel_b_offset < 0:
            raise ValueError('channel_a_offset ve channel_b_offset yapilandirilmali (>= 0)')
        self._invert = invert
        self._tick_count = 0
        self._lock = threading.Lock()

        self._channel_a = chip.get_line(channel_a_offset)
        self._channel_b = chip.get_line(channel_b_offset)
        self._channel_a.request(consumer=consumer, type=gpiod.LINE_REQ_EV_RISING_EDGE)
        self._channel_b.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_IN)

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop_event.is_set():
            # Kisa timeout: stop_event'i duzenli kontrol edebilmek icin
            # sonsuza kadar bloklamiyoruz.
            if self._channel_a.event_wait(sec=0, nsec=200_000_000):
                self._channel_a.event_read()
                b_level = self._channel_b.get_value()
                direction = decode_tick_direction(b_level, self._invert)
                with self._lock:
                    self._tick_count += direction

    def read_and_reset_ticks(self) -> int:
        with self._lock:
            ticks = self._tick_count
            self._tick_count = 0
        return ticks

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        self._channel_a.release()
        self._channel_b.release()
