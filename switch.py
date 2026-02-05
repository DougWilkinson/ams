# switch.py
# switch device with some additional features:
# pin: gpio Pin()
# trigger_device: a Device with binary_sensor state (trigger when "on")
# condition: a Device with binary_sensor state (allows switch to be turned on when condition state is "on")

from versions import versions
versions[__name__] = 7
# 5: refactored version (no hass_setup)
# 6: fixed trigger_device name
# 7: added support for no gpio use of Switch class

import time
from logger import debug
import asyncio
from device import Device
from system import start

delay_enabled = asyncio.Event()

# do nothing pin class

class NullPin:

	def on(self):
		pass

	def off(self):
		pass

class Switch:
	def __init__(self, name, pin=NullPin(), off_delay=0, trigger_device=None, condition=None) -> None:

		self.switch = Device(name, "OFF", dtype="switch")
		self.pin = pin

		self.last_triggered = -1
		self.trigger_device = trigger_device

		self.off_delay = off_delay

		self.condition = condition

		start(self.state_handler)
		start(self.trigger_handler)
		start(self.delay_handler)

		debug("switch: {} on pin {}".format(name, pin) )

	async def state_handler(self):
		async for _ , ev in self.switch.q:
			debug("state ev: {}".format(ev))
			if "ON" in ev:
				debug("switch: ON")
				if self.off_delay:
					delay_enabled.set()
				self.pin.on()
				continue
			self.pin.off()
			debug("switch: OFF")

	async def trigger_handler(self):
		debug("trigger_handler: running")

		async for _, event in self.trigger_device.q:
			debug("trigger_handler: {} - {}".format(self.trigger_device.name, event))
		
			if event == "ON":
				debug("trigger ON")

				if self.condition and self.condition.state != "ON":
					debug("switch: ON event triggered, condition not met")
					continue

				if self.switch.state == "OFF":
					self.last_triggered = time.time()
					if self.off_delay:
						delay_enabled.set()
					self.switch.set_state("ON")
				else:
					debug("switch: retriggered")
					self.last_triggered = time.time()

			if event == "OFF" and self.switch.state == "ON":
				debug("trigger OFF")
				
				if not self.off_delay:
					self.switch.set_state("OFF")

	async def delay_handler(self):
		while True:
			await delay_enabled.wait()
			passed = 0
			while passed < self.off_delay:
				await asyncio.sleep(self.off_delay - passed)
				passed = time.time() - self.last_triggered

			self.switch.set_state("OFF")
			delay_enabled.clear()
