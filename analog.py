# analog.py
# reading analog gpio value

from versions import versions
versions[__name__] = 5
# 5: refactored version (no hass_setup)

import asyncio
from machine import Pin, ADC
from device import Device
from system import start, info

class Analog:

	def __init__(self, name, pin, diff=0.3, poll_seconds=None, k=159.3, units="v"):

		self.adc = ADC(Pin(pin))
		self.poll_seconds = poll_seconds		
		self.k = k
		self.diff = diff
		self.last_value = -1
		self.analog = Device(name, "0", units=units)
		if poll_seconds:
			start(self.adc_handler )			

	def adc_read(self) -> float:
		val = round(self.adc.read()/self.k,2)
		if abs(self.last_value - val) > self.diff:
			self.last_value = val
			self.analog.set_state(val)
		return val

	async def adc_handler(self):
		while True:
			self.adc_read()
			await asyncio.sleep(self.poll_seconds)
