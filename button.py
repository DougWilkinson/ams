# button.py

version = (1,0,0)

from machine import Pin
import time
from alog import info, debug, error, started, stopped, exited
import uasyncio as asyncio

class Button:
	def __init__(self, name, pin=15, pullup=False, invert=False ):
		started(name)
		self.name = name
		self.invert = invert
		if pullup:
			self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
		else:
			self.pin = Pin(pin, Pin.IN)
		# force first read
		self.last = not self.read_pin()

	async def wait(self):
		# wait for button release
		info("button wait for release")
		while self.read_pin():
			await asyncio.sleep(0)
		# wait for button press
		info("button wait for press")
		while not self.read_pin():
			await asyncio.sleep(0)
		info("button pressed")

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)
