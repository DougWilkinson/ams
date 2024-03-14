# binary_sensor.py

version = (1,0,0)

from machine import Pin
import time
from alog import info, debug, error, started, stopped, exited
from aconfig import setup, pubstate
import asyncio

class BinarySensor:
	def __init__(self, name, settings) -> None:
		self.name = name
		pin_num = settings.get('pin', None)
		if not pin_num:
			raise ValueError
		self.pin = Pin(pin_num, Pin.IN)
		self.invert = settings.get('invert', 0) > 0		# default False
		# force first read/pub
		self.last = not self.read_pin()
		setup(name, self.handler, entity=self.name)

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)

	async def handler(self,event):
		started(self.name)
		while True:
			try:
				new = self.read_pin()
				if new != self.last:
					await pubstate(self.name, "ON" if new else "OFF")
					self.last = new
			except asyncio.CancelledError:
				stopped(self.name)
				return
			except:
				error('binary_sensor: error')
			await asyncio.sleep(0)
		exited(self.name)