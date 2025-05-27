# mini3d.py
# For esp32 and sh1106 in red case

from versions import versions
versions[__name__] = 1

#from framebuf import MONO_VLSB
from machine import Pin, SoftI2C
from core import info, latch

from sh1106 import SH1106_I2C
#from ssd1306 import SSD1306_I2C

#from blitplus import BlitClock
from hass import ha_setup
from device import Device
import asyncio

from clock3da import Clock3D

latch = asyncio.Event() 

sh1106_i2c = SoftI2C(scl=Pin(22),sda=Pin(21))

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

# sh_clock = BlitClock("sh1106", width=64, height=64, display=sh_display, bitmap=MONO_VLSB, hand=2)

sh_clock = Clock3D("mini3d", display=sh_display, scale=0.44)



async def start(hostname):
		await latch.wait()
