# mini3d.py
# For esp32-s3 mini and sh1106 in red case

from versions import versions
versions[__name__] = 12
# 10: converted to new standard
# 11: added on/off handling back in
# 12: added vl53l0x support

from vl53l0x import VL53L0X
from machine import I2C, Pin

from machine import Pin, SoftI2C

from system import start
from logger import info
from sh1106 import SH1106_I2C
from clock3dblit import Clock

from device import Device

info("cubeclock: loading")

sh1106_i2c = SoftI2C(scl=Pin(12),sda=Pin(13))

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

#sh_clock = Clock3D("cubeclock", display=sh_display, scale=0.44)
sh_clock = Clock("mini3d", sh_display)

forecast = Device("hass/weather/forecast", "", publish=False, dtype="mqtt" )
forecast.set_state("------------")

temperature = Device("hass/weather/temperature", "", publish=False, dtype="mqtt" )
temperature.set_state("--.-")

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


vlx_i2c = I2C(scl=Pin(8), sda=Pin(9))
vlx_sensor = VL53L0X("laptop", vlx_i2c, poll_seconds=1, min=1, max=500)

vlx_device = Device("laptop_open", "OFF", dtype="binary_sensor" )

async def update_vlx():
	info("update_vlx: running")
	
	if vlx_sensor.in_range():
		vlx_device.set_state("ON")
	else:
		vlx_device.set_state("OFF")
	
	vlx_device.needs_publishing.set()

	while True:
		await vlx_sensor.wait_for(in_range=True, count=3)
		vlx_device.set_state("ON")
		
		await vlx_sensor.wait_for(in_range=False, count=3)
		vlx_device.set_state("OFF")

start(update_vlx)

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
