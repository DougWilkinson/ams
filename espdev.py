#espdev.py
# pin 2 for 8266 and esp32-wroom devkits

from machine import Pin
import asyncio
from time import sleep

async def blink(wlan):
	statusled = Pin(2, Pin.OUT, 0)
	# 200 is wifi not connected
	status = 200
	while True:
		for i in range(2):
			statusled.value(i)
			await asyncio.sleep_ms(status)
		sleep(.05)
		status = 3000 if wlan.isconnected() else 200

