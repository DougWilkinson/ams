# neo.py

# 2,1,0: ledmatrix to async
version = (2,1,0)

import uasyncio as asyncio
from alog import info, offset_time
# notifier is hass
import hass
from matrixclock import MatrixClock

clock = asyncio.Event()
text = asyncio.Event()
display = MatrixClock("matrixclock", pin=13, num_leds=255, clock_trig=clock, text_trig=text)
display.clock = (0,2,2)

async def start(hostname):
	info("matrixclock: hostname")
	trigger_times = {"1": clock, "20": text, "54": clock }
	while True:
		currsec = str(offset_time()[5])
		if currsec not in trigger_times:
			await asyncio.sleep_ms(500)
			continue
		trigger_times[currsec].set()
