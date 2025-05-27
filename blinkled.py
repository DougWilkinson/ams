#blinkled.py

from machine import Pin
import asyncio
from time import sleep
from os import uname

class OffLed:
	def __init__(self, pin):
		self.pin = pin
	
	def write(self):
		self.pin.value(0)

class OnLed:
	def __init__(self, pin):
		self.pin = pin
	
	def write(self):
		self.pin.value(1)

if "ESP32S3" in uname().machine:
	from neopixel import NeoPixel

	off_led = NeoPixel(Pin(48), 1	)
	off_led[0] = (0,0,0)
	on_led = NeoPixel(Pin(48), 1	)
	on_led[0] = (0,0,20)

if "ESP32S2" in uname().machine:
	off_led = OffLed(Pin(15, Pin.OUT))
	on_led = OnLed(Pin(15, Pin.OUT))

if "ESP8266" in uname().machine or "ESP32 " in uname().machine:
	off_led = OffLed(Pin(2, Pin.OUT))
	on_led = OnLed(Pin(2, Pin.OUT))

async def wifi_status(wlan):

	# 200 is wifi not connected
	status = 200

	while True:
		off_led.write()
		await asyncio.sleep_ms(status)
		on_led.write()
		await asyncio.sleep_ms(status)
		sleep(.05)
		status = 3000 if wlan.isconnected() else 200

