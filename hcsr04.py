# hctray.py

# HC-SR04 sonic distance 
version = (1,0,0)

from machine import Pin
from time import sleep_us, ticks_us
from core import info, debug, error, started, stopped, exited
import asyncio
from device import Device
from hass import ha_setup

class HCTray:
	def __init__(self, name="tray", echo_pin=13, trig_pin=15, invert=False ):
		started(name)
		self.name = name
		self.invert = invert
		self.trig_pin = Pin(trig_pin, Pin.OUT, value=0)
		self.echo_pin = Pin(echo_pin, Pin.IN)
		#self.measure()
		# force first read
		self.tray = Device(name, 0, dtype="binary_sensor", notifier=ha_setup)
		self._on = asyncio.Event()
		self._off = asyncio.Event()
		if self.tray.state:
			self._on.set()
		else:
			self._off.set()
		#asyncio.create_task(self.update_state())		

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

	def measure(self):
		self.trig_pin.on()
		sleep_us(10)
		self.trig_pin.off()
		echo_start = ticks_us()
		for i in range(100000):
			echo_end = ticks_us()
			if self.echo_pin.value():
				break
		return echo_end - echo_start
			
