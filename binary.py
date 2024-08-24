# binary.py

version = (2,0,0)
# 200: revised to work with ledlight/ledmotion

from machine import Pin
import time
from core import debug
import uasyncio as asyncio
from device import Device
from hass import ha_setup

class Binary:
	def __init__(self, name, pin, invert=False) -> None:
		self.name = name
		self.pin = Pin(pin, Pin.IN)
		self.invert = invert
		self.state = Device("{}".format(name), "OFF", dtype="binary_sensor", notifier_setup=ha_setup)
		asyncio.create_task(self.handler() )

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)

	async def handler(self):
		while True:
			if self.state.state == "OFF" and self.read_pin():
				debug("sensor: on")
				self.state.set_state("ON")
			if self.state.state == "ON" and not self.read_pin():
				debug("sensor: off")
				self.state.set_state("OFF")
			await asyncio.sleep_ms(300)
