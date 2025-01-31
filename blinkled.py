#blinkled.py

from machine import Pin
import asyncio
from time import sleep

async def blink(wlan):
	statusled = Pin(2, Pin.OUT, 0)
	# 200 is wifi not connected
	status = 200
	while True:
		statusled.value(0)
		await asyncio.sleep_ms(status)
		statusled.value(1)
		await asyncio.sleep_ms(status)
		sleep(.05)
		if wlan.isconnected():
			status = 3000
		else:
			status = 200

