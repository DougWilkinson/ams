# s3dev.py

from versions import versions
versions[__name__] = 1

from framebuf import MONO_VLSB
from machine import Pin, SoftI2C
from core import info, latch

from sh1106 import SH1106_I2C
from ssd1306 import SSD1306_I2C

from blitplus import BlitClock
from hass import ha_setup
from device import Device
import asyncio

from clock3da import Clock3D

from hx711 import HX711
from scale import Scale

# from tmclock import TMClock
# display = TMClock(data_pin=47, clock_pin=21, brightness=5)

from tm1637 import TM1637
display = TM1637("s3dev_tmclock", clock=True, data_pin=47, clock_pin=21, brightness=5)


sh1106_i2c = SoftI2C(scl=Pin(1),sda=Pin(2))

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

# sh_clock = BlitClock("sh1106", width=64, height=64, display=sh_display, bitmap=MONO_VLSB, hand=2)

sh_clock = Clock3D("s3dev_clock3d", display=sh_display, scale=0.44)


ssd1306_i2c = SoftI2C(scl=Pin(41),sda=Pin(42))

ssd1306_display = SSD1306_I2C(128, 64, ssd1306_i2c )
#ssd1306_display.invert(True)

oledclock = BlitClock("ssd1306",  display=ssd1306_display, bitmap=MONO_VLSB, hand=2, color=255)


ssd9_i2c = SoftI2C(scl=Pin(39),sda=Pin(40))

ssd9_display = SSD1306_I2C(128, 32, ssd9_i2c )
oledclock = BlitClock("ssd9",  display=ssd9_display, bitmap=MONO_VLSB, hand=2)

hx = HX711(hxclock_pin=4, hxdata_pin=5, k=229, max=9999, offset=1407, samples=5)

foodscale = Scale("foodscale", hx, diff=10)


async def start(hostname):
		await latch.wait()
