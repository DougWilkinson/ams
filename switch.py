# switch.py
# switch only for gpio

from versions import versions
versions[__name__] = 1

from machine import Pin
import time
from core import info, debug, error
import uasyncio as asyncio
from device import Device
from hass import ha_setup

class Switch:
	def __init__(self, name="relay", switch_pin=13) -> None:

		self.state = Device(name, "OFF", dtype="switch", notifier_setup=ha_setup)
		self.switch = Pin(switch_pin, Pin.OUT)
		self.switch.off()

		asyncio.create_task(self.state_handler() )
		debug("switch: {} on pin {}".format(name, switch_pin) )

	async def state_handler(self):
		async for _ , ev in self.state.q:
			debug("state ev: {}".format(ev))
			if "ON" in ev:
				debug("switch: ON")
				self.switch.on()
				continue
			self.switch.off()
			debug("switch: OFF")
