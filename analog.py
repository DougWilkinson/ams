# analog.py
# used with charger.py

from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
from sys import platform
from machine import Pin, ADC
from device import Device
from hass import ha_setup

# poll_seconds = 0 will not auto-update, 
# read_adc manually for value update

class Analog:

	def __init__(self, name, pin=None, diff=0.3, poll_seconds=60, k=159.3, units="v"):
		if 'esp32' in platform:
			if pin:
				self.adc = ADC(Pin(pin))
			else:
				raise UserWarning("pin # needed on esp32")
		if 'esp8266' in platform:
			self.adc = ADC(0)
		
		self.k = k
		self.diff = diff
		self.last_value = -1
		self.analog = Device(name, "0", units=units, notifier_setup=ha_setup)
		if poll_seconds:
			asyncio.create_task(self.adc_handler(poll_seconds) )			

	def adc_read(self) -> float:
		val = round(self.adc.read()/self.k,2)
		if abs(self.last_value - val) > self.diff:
			self.last_value = val
			self.analog.set_state(val)
		return val

	async def adc_handler(self, poll_seconds):
		while True:
			self.adc_read()
			await asyncio.sleep(poll_seconds)
