# binary.py

from versions import versions
versions[__name__] = 11
# 200: revised to work with ledlight/ledmotion
# 5: updated to new format (no ha_setup)
# 10: added checker "start" and "completed" coros to use with steppermotor/cover class
# 11: added pullup support for pin definition

from machine import Pin
from system import start
from logger import debug, info, error
import asyncio
from device import Device

class Binary:
	def __init__(self, name, pin, invert=False, pullup=0) -> None:
		self.name = name
		self.pin = Pin(pin, Pin.IN, pullup )
		self.invert = invert
		state = "ON" if self.read_pin() else "OFF"
		self.state = Device(name, state, dtype="binary_sensor")
		start(self.binary_handler )

	def read_pin(self):
		return (not self.pin.value()) if self.invert else (self.pin.value() > 0)

	async def binary_handler(self):
		info("binary_handler: running")
		while True:
			
			if self.state.state == "OFF" and self.read_pin():
				debug("{}: on".format(self.state.name) )
				self.state.set_state("ON")
			
			if self.state.state == "ON" and not self.read_pin():
				debug("{}: off".format(self.state.name) )
				self.state.set_state("OFF")
			
			await asyncio.sleep_ms(300)

	# start values to setup for checking
	def start(self):
		self.last_state = self.read_pin()

	# returns 0 if not at limit
	# returns 1 if limit reached
	def completed(self):
		current_state = self.read_pin()
		if current_state:
			error(f"{self.name}: limit reached" )
			return 1
		else:
			return 0
		
		# on to off is not considered complete (limit switch)
		self.last_state = current_state
		return 0