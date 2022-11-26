# Read pair of AHT10 Temp,RH sensors on Pi Pico / micropython
# J.Beale 26-Nov-2022

"""
Usage of this module:

avgCount = 10  # how many readings to average together
S = AHTPair()  # create sensor-reading object
S.initSensors([17,16,15,14]) # scl1,sda1, scl2,sda2
while True:
    outs = S.getTH(avgCount)
    print(outs)
"""

import utime
from machine import Pin, I2C
import ahtx0 # https://github.com/targetblank/micropython_ahtx0

# getTH() : get average of N readings of Temp and RH from two sensors
class AHTPair:
    def getTH(self,N):
        Tsum0 = 0
        Hsum0 = 0
        Tsum1 = 0
        Hsum1 = 0
        for i in range(N):
            Tsum0 += self.s0.temperature
            Tsum1 += self.s1.temperature
            Hsum0 += self.s0.relative_humidity
            Hsum1 += self.s1.relative_humidity
            utime.sleep(1)

        T0 = Tsum0 / N
        H0 = Hsum0 / N
        T1 = Tsum1 / N
        H1 = Hsum1 / N
        outs = ("%0.3f,%0.3f, %0.3f,%0.3f" % (T0,T1,H0,H1))
        return outs

    def initSensors(self, pins):
        i2c0 = I2C(0, scl=Pin(pins[0]), sda=Pin(pins[1]), freq=400_000)
        i2c1 = I2C(1, scl=Pin(pins[2]), sda=Pin(pins[3]), freq=400_000)
        self.s0 = ahtx0.AHT10(i2c0)
        self.s1 = ahtx0.AHT10(i2c1)

# =============================
