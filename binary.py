# binary.py

from versions import versions
versions[__name__] = 3
# 200: revised to work with ledlight/ledmotion

from machine import Pin
import time
from core import debug
import uasyncio as asyncio
from device import Device
from hass import ha_setup

class Binary:
	def __init__(self, name, pin, invert=False, notifier=ha_setup) -> None:
		self.pin = Pin(pin, Pin.IN)
		self.invert = invert
		state = "ON" if self.read_pin() else "OFF"
		self.state = Device(name, state, dtype="binary_sensor", notifier_setup=notifier)
		asyncio.create_task(self.handler() )

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)

	async def handler(self):
		while True:
			if self.state.state == "OFF" and self.read_pin():
				debug("{}: on".format(self.state.name) )
				self.state.set_state("ON")
			if self.state.state == "ON" and not self.read_pin():
				debug("{}: off".format(self.state.name) )
				self.state.set_state("OFF")
			await asyncio.sleep_ms(300)
