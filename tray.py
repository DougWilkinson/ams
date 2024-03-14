# tray.py

# added easier access to is_on and is_off status
version = (1,0,1)

from machine import Pin
import time
from alog import info, debug, error, started, stopped, exited
import asyncio
from device import Device
from hass import ha_setup

class Tray:
	def __init__(self, name, pin=13, invert=True ):
		started(name)
		self.name = name
		self.invert = invert
		self.pin = Pin(pin, Pin.IN)
		# force first read
		self.tray = Device(name, self.read_pin(), dtype="binary_sensor", notifier=ha_setup)
		self._on = asyncio.Event()
		self._off = asyncio.Event()
		if self.tray.state:
			self._on.set()
		else:
			self._off.set()
		asyncio.create_task(self.update_state())		

	def is_on(self):
		return self._on.is_set()
	
	def is_off(self):
		return self._off.is_set()
	
	async def update_state(self):
		while True:
			while self.read_pin():
				await asyncio.sleep(1)
			info("tray is off")
			self.tray.publish.set()
			self._on.clear()
			self._off.set()
			await asyncio.sleep(1)
			while not self.read_pin():
				await asyncio.sleep(1)
			info("tray is on")
			self.tray.publish.set()
			self._on.set()
			self._off.clear()
			await asyncio.sleep(1)

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)
