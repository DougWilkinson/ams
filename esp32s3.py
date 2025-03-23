# esp32s3.py
# uses neopixel

from machine import Pin
import asyncio
from time import sleep
from neopixel import NeoPixel

async def blink(wlan):
	off_led = NeoPixel(Pin(48), 1	)
	off_led[0] = (0,0,0)
	on_led = NeoPixel(Pin(48), 1	)
	on_led[0] = (0,0,20)
	# 200 is wifi not connected
	status = 200
	while True:
		off_led.write()
		await asyncio.sleep_ms(status)
		on_led.write()
		await asyncio.sleep_ms(status)
		sleep(.05)
		status = 3000 if wlan.isconnected() else 200
