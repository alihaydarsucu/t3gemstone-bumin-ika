"""Linux sysfs PWM (/sys/class/pwm/pwmchipN/pwmM) uzerinden gercek
donanimsal PWM ureten kucuk yardimci sinif.

Gemstone O1'de kullandigimiz iki bagimsiz eCAP kanali: GPIO12 (ecap0) ->
pwmchip0/pwm0, GPIO18 (ecap2) -> pwmchip2/pwm0 (bkz. /boot/uEnv.txt
`overlays=`). Bu sinif export/period/duty_cycle/enable dosyalarini
yazarak bu kanallari suruyor.

export cagrisi yeni bir udev "add" olayi tetikler; izinleri duzelten udev
kurali (bkz. docs/hardware notlari) bu olaya asenkron tepki verir --
genelde birkac ms icinde ama garanti degil. O yuzden export'tan sonra
ilk yazidan once dosyanin yazilabilir olmasini kisa bir sure bekleyip
deniyoruz (_wait_writable); aksi halde export'u biz tetikledigimiz her
seferde (ör. reboot sonrasi ilk calistirma) araya giren bir yaris
durumu (race condition) "Permission denied" olarak ortaya cikabiliyor.
"""

import os
import time


class SysfsPwm:

    _BASE = '/sys/class/pwm'

    def __init__(self, chip: int, channel: int, period_ns: int = 1_000_000):
        if chip < 0 or channel < 0:
            raise ValueError('chip ve channel yapilandirilmali (>= 0)')
        self._chip_path = f'{self._BASE}/pwmchip{chip}'
        self._pwm_path = f'{self._chip_path}/pwm{channel}'
        self._period_ns = period_ns

        if not os.path.isdir(self._pwm_path):
            self._write_chip('export', channel)
            self._wait_writable('period')

        # Period'u degistirmeden once enable'i kapatmak, "duty_cycle onceki
        # period'dan buyuk" gibi sysfs hatalarini onler.
        try:
            self._write('enable', 0)
        except OSError:
            pass
        self._write('period', period_ns)
        self._write('duty_cycle', 0)
        self._write('enable', 1)

    def _wait_writable(self, name: str, timeout_s: float = 1.0):
        path = f'{self._pwm_path}/{name}'
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if os.path.exists(path) and os.access(path, os.W_OK):
                return
            time.sleep(0.02)

    def _write_chip(self, name: str, value):
        with open(f'{self._chip_path}/{name}', 'w') as f:
            f.write(str(value))

    def _write(self, name: str, value):
        with open(f'{self._pwm_path}/{name}', 'w') as f:
            f.write(str(value))

    def set_duty_percent(self, percent: float):
        percent = max(0.0, min(100.0, percent))
        duty_ns = int(self._period_ns * percent / 100.0)
        self._write('duty_cycle', duty_ns)

    def release(self):
        try:
            self._write('enable', 0)
        except OSError:
            pass
