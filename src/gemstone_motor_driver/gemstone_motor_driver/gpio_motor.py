"""MX1508 (Harezmi karti uzerindeki dual H-bridge) cikisini libgpiod ile
suren sinif.

MX1508'in her kanali 2 dijital giris bekler (IN1/IN2 -- Harezmi + Deneyap
pin haritasinda D12/D13 motor1, D14/D15 motor2 idi, simdi Gemstone GPIO'suna
tasiniyor):
    IN1=HIGH, IN2=LOW  -> ileri
    IN1=LOW,  IN2=HIGH -> geri
    IN1=IN2=LOW         -> coast (bosta, serbest doner)

ONEMLI (hiz kontrolu hakkinda): Bu implementasyon SADECE yon kontrolu yapar
(bang-bang: tam hiz ileri / tam hiz geri / dur). Gercek degisken hiz (PWM)
icin Gemstone'un donanimsal PWM cikisi (bkz. docs.t3gemstone.org PWM overlay)
gerekiyor -- libgpiod salt dijital GPIO'dur, PWM uretmez. Python
seviyesinde "yazilimsal PWM" (timer ile GPIO'yu hizli ac/kapa) da bir secenek
ama DC motor icin gerekli birkaç yuz Hz - birkaç kHz tasiyici frekansi
Python/rclpy timer'indan guvenilir sekilde alinamaz (jitter/CPU maliyeti
yuksek), bu yuzden bilerek eklenmedi. PWM-uyumlu fiziksel pinler
netlesince (karti kontrol edip `/sys/class/pwm/` bakildiginda) bu sinif
sysfs PWM yazacak sekilde genisletilebilir; disaridan cagrilan `drive()`
arayuzu degismeyecek.
"""

try:
    import gpiod
except ImportError:  # pragma: no cover - sadece Linux/karti disinda (ör. gelistirme makinesi)
    gpiod = None


class GpioHBridgeMotor:

    def __init__(self, chip: 'gpiod.Chip', in1_line_offset: int, in2_line_offset: int,
                 consumer: str = 'gemstone_motor_driver', invert: bool = False):
        if in1_line_offset < 0 or in2_line_offset < 0:
            raise ValueError('in1_line_offset ve in2_line_offset yapilandirilmali (>= 0)')
        self._invert = invert
        self._in1 = chip.get_line(in1_line_offset)
        self._in2 = chip.get_line(in2_line_offset)
        self._in1.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
        self._in2.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

    def drive(self, percent: float, deadband_percent: float = 5.0):
        """percent: -100..100 (yon icin isaret, buyukluk su an yok sayiliyor
        -- bkz. modul docstring'i). deadband_percent altindaki degerler
        dur (coast) olarak yorumlanir, motorun titremesini onler.
        """
        if self._invert:
            percent = -percent
        forward = percent > deadband_percent
        backward = percent < -deadband_percent
        self._in1.set_value(1 if forward else 0)
        self._in2.set_value(1 if backward else 0)

    def stop(self):
        self._in1.set_value(0)
        self._in2.set_value(0)

    def release(self):
        self._in1.release()
        self._in2.release()
