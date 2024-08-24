# tray.py

# added easier access to is_on and is_off status
version = (1,0,1)

from machine import Pin
import time
from core import info, debug, error, started, stopped, exited
import uasyncio as asyncio
from device import Device
from hass import ha_setup

class Tray:
	def __init__(self, name, pin=13, invert=True ):
		started(name)
		self.name = name
		self.invert = invert
		self.pin = Pin(pin, Pin.IN)
		# force first read
		self.tray = Device(name, "", dtype="binary_sensor", notifier_setup=ha_setup)
		self.read_pin()
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
			self._on.clear()
			self._off.set()
			await asyncio.sleep(1)
			while not self.read_pin():
				await asyncio.sleep(1)
			info("tray is on")
			self._on.set()
			self._off.clear()
			await asyncio.sleep(1)

	def read_pin(self):
		value = (not self.pin.value()) if self.invert else (self.pin.value() > 0)
		self.tray.set_state("ON" if value else "OFF")
		return value