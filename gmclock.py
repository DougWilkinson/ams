# gmclock.py

from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
from core import info, offset_time, latch, hostname
from tick import Tick
from cover import Cover
from binary import Binary

# ESP8266 pin based config
# chime_sensor = Binary("gmclock_chimes", pin=4, invert=True)
# chime = Cover("gmclock_chime", enable_pin=12, step_pin=15, 
# 			  dir_pin=13, delay=1250, backoff_steps=2, max_steps=550 )
# clock = Tick(hostname, tick_pin=5, pause_pin=14, samples=60)

# ESP32-S2 mini pin configuration
chime_sensor = Binary("gmclock_chimes", pin=39, invert=True)
chime = Cover("gmclock_chime", enable_pin=37, step_pin=33, 
			  dir_pin=35, delay=1250, backoff_steps=2, max_steps=550 )
clock = Tick(hostname, tick_pin=16, pause_pin=18, samples=60)

async def start(hostname):
		await latch.wait()
