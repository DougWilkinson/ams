# cable.py

from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
from core import debug
from machine import Pin
from time import sleep_ms, ticks_diff, ticks_ms
from device import Device
from hass import ha_setup

class Cable:

	# probe_pin: connected through cable to test connectedness
	# used to pulse and read ADC value
	# adc_read = function that returns a voltage from ADC
	# Connected - voltage ~ 1-2 v
	# not connected voltage > 3 v
	def __init__(self, name, probe_pin, adc_read, 
				adc_poll_ms=100, k=159.3,
				adc_diff=0.1, threshold=3.5 ):
		self.k = k
		self.adc_read = adc_read
		self.adc_poll_ms = adc_poll_ms
		# probe must have both probe pin and disable pin to work
		self.probe_pin = Pin(probe_pin, Pin.OUT)
		self.threshold = threshold
		self.cable = Device(name, "OFF", dtype="binary_sensor", notifier_setup=ha_setup )
		asyncio.create_task(self.probe_handler() )

	def poll(self) -> bool:
		self.probe_pin.value(1)
		sleep_ms(1)
		volts = self.adc_read()
		self.probe_pin.value(0)
		# off if > threshold, on if < threshold
		if volts > self.threshold:
			return False
		else:
			return True

	async def probe_handler(self):
		while True:
			self.cable.set_state("OFF")
			debug("Cable is disconnected (off)")
			# wait until over threshold (cable on)
			while not self.poll():
				await asyncio.sleep_ms(self.adc_poll_ms)
			await asyncio.sleep(2)
			self.cable.set_state("ON")
			debug("Cable is connected (on)")
			# wait for cable to disconnect
			while self.poll():
				await asyncio.sleep_ms(self.adc_poll_ms)
			await asyncio.sleep(2)
