"""L298N (veya IN1/IN2 tipi baska bir dual H-bridge modulu) cikisini
libgpiod ile suren sinif.

Bu tip suruculerin her kanali 2 dijital giris bekler (IN1/IN2, ya da
bazi kompakt klonlarda A1/A2 - B1/B2 olarak etiketlenir, mantik ayni):
    IN1=HIGH, IN2=LOW  -> ileri
    IN1=LOW,  IN2=HIGH -> geri
    IN1=IN2=LOW         -> coast (bosta, serbest doner)

Hiz kontrolu: yon (IN1/IN2) libgpiod ile dijital surulur. Hiz icin
opsiyonel bir `pwm` (bkz. sysfs_pwm.SysfsPwm) verilirse, ENA/ENB'ye
gercek donanimsal PWM (Gemstone'un ecap0/epwm1 overlay'leri, bkz.
sysfs_pwm.py) yazilir. `pwm=None` ise (varsayilan) davranis eskisiyle
ayni: ENA/ENB kartta jumper ile sabit HIGH kabul edilir, sadece
yon degisir, hiz her zaman tam guctur (bang-bang).
"""

try:
    import gpiod
except ImportError:  # pragma: no cover - sadece Linux/karti disinda (ör. gelistirme makinesi)
    gpiod = None

from gemstone_motor_driver.sysfs_pwm import SysfsPwm


class GpioHBridgeMotor:

    def __init__(self, chip: 'gpiod.Chip', in1_line_offset: int, in2_line_offset: int,
                 consumer: str = 'gemstone_motor_driver', invert: bool = False,
                 pwm: 'SysfsPwm | None' = None):
        if in1_line_offset < 0 or in2_line_offset < 0:
            raise ValueError('in1_line_offset ve in2_line_offset yapilandirilmali (>= 0)')
        self._invert = invert
        self._pwm = pwm
        self._in1 = chip.get_line(in1_line_offset)
        self._in2 = chip.get_line(in2_line_offset)
        self._in1.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
        self._in2.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

    def drive(self, percent: float, deadband_percent: float = 5.0):
        """percent: -100..100. `pwm` verilmediyse buyukluk yok sayilir
        (bang-bang, tam hiz). `pwm` verildiyse buyukluk ENA/ENB'ye duty
        cycle olarak yazilir -- gercek degisken hiz.
        deadband_percent altindaki degerler dur (coast) olarak yorumlanir,
        motorun titremesini onler.
        """
        if self._invert:
            percent = -percent
        forward = percent > deadband_percent
        backward = percent < -deadband_percent
        self._in1.set_value(1 if forward else 0)
        self._in2.set_value(1 if backward else 0)
        if self._pwm is not None:
            self._pwm.set_duty_percent(abs(percent) if (forward or backward) else 0.0)

    def stop(self):
        self._in1.set_value(0)
        self._in2.set_value(0)
        if self._pwm is not None:
            self._pwm.set_duty_percent(0.0)

    def release(self):
        self._in1.release()
        self._in2.release()
        if self._pwm is not None:
            self._pwm.release()
