# blinkrgb.py

from machine import Pin
import asyncio
from time import sleep
from neopixel import NeoPixel

async def blink(wlan):
	statusled = NeoPixel(Pin(48), 1	)
	# 200 is wifi not connected
	status = 200
	while True:
		statusled.fill((0,0,0))
		statusled.write()
		await asyncio.sleep_ms(status)
		statusled.fill((0,0,20))
		statusled.write()
		await asyncio.sleep_ms(status)
		sleep(.05)
		if wlan.isconnected():
			status = 3000
		else:
			status = 200
