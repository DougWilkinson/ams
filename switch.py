# switch.py
# gpio switch

from versions import versions
versions[__name__] = 1

from machine import Pin
import time
from core import info, debug, error
import asyncio
from device import Device
from hass import ha_setup

delay_enabled = asyncio.Event()

class Switch:
	def __init__(self, name="relay", switch_pin=13, off_delay=0, trigger_device=None, condition=None) -> None:

		self.switch = Device(name, "OFF", dtype="switch", notifier_setup=ha_setup)
		self.switch_pin = Pin(switch_pin, Pin.OUT)
		self.switch_pin.off()

		self.last_triggered = -1

		if condition:
			self.condition = condition
		else:
			self.condition = Device("conditoin", "ON")

		asyncio.create_task(self.trigger_handler(trigger_device, off_delay) )

		asyncio.create_task(self.delay_handler(off_delay) )

		asyncio.create_task(self.state_handler(off_delay) )

		debug("switch: {} on pin {}".format(name, switch_pin) )

	async def state_handler(self, off_delay):
		async for _ , ev in self.switch.q:
			debug("state ev: {}".format(ev))
			if "ON" in ev:
				debug("switch: ON")
				if off_delay:
					delay_enabled.set()
				self.switch_pin.on()
				continue
			self.switch_pin.off()
			debug("switch: OFF")

	async def trigger_handler(self, trigger, off_delay):

		async for _, event in trigger.q:
			debug("{} - {}".format(trigger.name, event))
		
			if event == "ON" and self.condition.state == "ON":
				if self.switch.state == "OFF":
					self.last_triggered = time.time()
					if off_delay:
						delay_enabled.set()
					self.switch.set_state("ON")
				else:
					debug("switch: retriggered")
					self.last_triggered = time.time()

			if event == "OFF" and self.switch.state == "ON":
				debug("trigger off")
				if not off_delay:
					self.switch.set_state("OFF")

	async def delay_handler(self, off_delay):
		while True:
			await delay_enabled.wait()
			passed = 0
			while passed < off_delay:
				await asyncio.sleep(off_delay - passed)
				passed = time.time() - self.last_triggered

			self.switch.set_state("OFF")
			delay_enabled.clear()
