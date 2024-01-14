# tray.py

version = (1,0,0)

from machine import Pin
import time
from alog import info, debug, error, started, stopped, exited
import asyncio
from device import Device
from hass import BinarySensor

class Tray:
	def __init__(self, name, pin=13, invert=True ):
		started(name)
		self.name = name
		self.invert = invert
		self.pin = Pin(pin, Pin.IN)
		# force first read
		self.tray = Device(name, self.read_pin(), notifier=BinarySensor)
		self.tray_on = asyncio.Event()
		self.tray_off = asyncio.Event()
		if self.tray.state:
			self.tray_on.set()
		else:
			self.tray_off.set()
		asyncio.create_task(self.update_state())		

	async def update_state(self):
		while True:
			while self.read_pin():
				await asyncio.sleep(1)
			info("tray is off")
			self.tray.publish.set()
			self.tray_on.clear()
			self.tray_off.set()
			await asyncio.sleep(1)
			while not self.read_pin():
				await asyncio.sleep(1)
			info("tray is on")
			self.tray.publish.set()
			self.tray_on.set()
			self.tray_off.clear()
			await asyncio.sleep(1)

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)
