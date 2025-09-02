# touchpin.py

from versions import versions
versions[__name__] = 1

from machine import Pin, TouchPad
from device import Device
import time
from logger import info
import asyncio

class TouchPin:
	def __init__(self, name, pin=15, on_value=999999, off_value=0, invert=False ):
		self.name = name
		self.invert = invert
		self.on_value = on_value
		self.off_value = off_value
		self.last_value = -1
		self.pin = TouchPad(Pin(pin))

	def read_pin(self):
		self.last_value = self.pin.read()
		if self.last_value < self.off_value:
			return True if self.invert else False
		if self.last_value >= self.on_value:
			return False if self.invert else True

	async def wait(self):
		# wait for button release
		info("{} wait for release".format(self.name))
		while self.read_pin():
			await asyncio.sleep(0)
		info("{} released value: {}".format(self.name, self.last_value) )
		# wait for button press
		info("{} wait for press".format(self.name))
		while not self.read_pin():
			await asyncio.sleep(0)
		info("{} pressed value: {}".format(self.name, self.last_value) )
