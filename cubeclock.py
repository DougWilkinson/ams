# cubeclock.py
# super mini s3 and sh1106 in office cube

from versions import versions
versions[__name__] = 1

#from framebuf import MONO_VLSB
from machine import Pin, SoftI2C
from core import info, latch

from touchpin import TouchPin

from sh1106 import SH1106_I2C
#from ssd1306 import SSD1306_I2C

#from blitplus import BlitClock
from hass import ha_setup
from device import Device
import asyncio
from flag import set, get
from clock3da import Clock3D

latch = asyncio.Event() 

sh1106_i2c = SoftI2C(scl=Pin(12),sda=Pin(13))

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

# sh_clock = BlitClock("sh1106", width=64, height=64, display=sh_display, bitmap=MONO_VLSB, hand=2)

sh_clock = Clock3D("cubeclock", display=sh_display, scale=0.44)

up_button = TouchPin("up_button", pin=6, on_value=19500, off_value=18500)
down_button = TouchPin("down_button", pin=7, on_value=18000, off_value=16000)	

# raw flag value for timezone saved here
timezone = Device("set_timezone", "29", save_state=True)

def show_timezone():
	sh_display.fill_rect(0, 0, 128, 8, 0)
	sh_display.text("timezone: {}   ".format(get("timezone") - 24), 0, 0)
	timezone.set_state(get("timezone") )

async def increase_timezone():
	while True:
		await up_button.wait()
		set("timezone", get("timezone") + 1)
		show_timezone()

async def decrease_timezone():
	while True:
		await down_button.wait()
		set("timezone", get("timezone") - 1)
		show_timezone()

asyncio.create_task(increase_timezone())
asyncio.create_task(decrease_timezone())

show_timezone()

async def start(hostname):
		await latch.wait()
