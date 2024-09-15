# trinity.py

from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
from core import info, offset_time, latch, hostname
from matrixclock import MatrixClock

display = MatrixClock(hostname, pin=13, num_leds=255, clock_color=(0,2,2), text_color=(0,0,1))

async def start(hostname):
		await latch.wait()
