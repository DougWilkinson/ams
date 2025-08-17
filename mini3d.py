# mini3d.py
# For esp32-s3 mini and sh1106 in red case

from versions import versions
versions[__name__] = 1

from machine import Pin, SoftI2C
import asyncio
import time

from hass import subscribe_name
from settings import info, debug, error, config, start, get_profiles
from sh1106 import SH1106_I2C
from clock3da import Clock3D

from device import Device

info("cubeclock: loading")

sh1106_i2c = SoftI2C(scl=Pin(12),sda=Pin(13))

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

sh_clock = Clock3D("cubeclock", display=sh_display, scale=0.44)

forecast = Device("hass/weather/forecast", "" )
forecast.set_state("------------")
subscribe_name(forecast)

temperature = Device("hass/weather/temperature", "" )
temperature.set_state("--.-")
subscribe_name(temperature)

async def update_weather():
	info("update_weather: running")
	async for _, ev in forecast.q:
		# clear top row
		sh_display.fill_rect(0, 0, 128, 8, 0)
		# clear bottom row
		sh_display.fill_rect(0, 56, 128, 64, 0)

		sh_display.text(forecast.state, 0, 56)
		sh_display.text(temperature.state, 128 - (8 * len(temperature.state) ), 0)
		sh_display.show()

start(update_weather)


# #from framebuf import MONO_VLSB
# from machine import Pin, SoftI2C
# from core import info, latch

# from sh1106 import SH1106_I2C
# #from ssd1306 import SSD1306_I2C

# #from blitplus import BlitClock
# from hass import ha_setup
# from device import Device
# import asyncio

# from clock3da import Clock3D

# latch = asyncio.Event() 

# sh1106_i2c = SoftI2C(scl=Pin(22),sda=Pin(21))

# sh_display = SH1106_I2C(128, 64, sh1106_i2c )

# # sh_clock = BlitClock("sh1106", width=64, height=64, display=sh_display, bitmap=MONO_VLSB, hand=2)

# sh_clock = Clock3D("mini3d", display=sh_display, scale=0.44)



# async def start(hostname):
# 		await latch.wait()
