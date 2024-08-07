# ina219.py

version = (2,0,9)
# 209: requires device object to use .pin attribute

import uasyncio as asyncio
from machine import Pin
from device import Device
from hass import ha_setup
from alog import error, debug

safe_current = asyncio.Event()
safe_current.set()

# i2c object defined (required)
# trip_device: a switch device (turns off when trip_threshold_amps exceeded
# trip_threshold_amps: value to exceed to shutoff trip pin object 
# diff: minimum value for updates
# k: multiplier for Ampere conversion
class INA219:
	def __init__(self, name, i2c, trip_device, trip_threshold_amps=0.6, diff=0.1, k=0.0000214292):
		self.i2c = i2c
		self.address = 0x40
		self.write_register(0x05, 16793)
		self.write_register(0, 2463)
		self.k = k
		self.diff = diff
		self.amperage = Device(name, "0.0", units="A", notifier_setup=ha_setup)
		self.threshold = trip_threshold_amps
		
		# trip device is "switchmotion"
		# trip_device.state is Davice()
		# trip_device.switch is Pin()
		self.trip_device = trip_device
		self.trip_state = Device("quest2_tripped", "OFF", dtype="binary_sensor", notifier_setup=ha_setup)
		
		asyncio.create_task(self.amperage_handler())
		asyncio.create_task(self.tripped_handler())
		
	def write_register(self, register, register_value):
		register_bytes = bytearray([(register_value >> 8) & 0xFF, register_value & 0xFF])
		self.i2c.writeto_mem(self.address, register, register_bytes)

	def read_register(self, register):
		register_bytes = self.i2c.readfrom_mem(self.address, register, 2)
		register_value = int.from_bytes(register_bytes, 'big')
		if register_value > 32767:
			register_value -= 65536
		return register_value

	async def tripped_handler(self):
		while True:
			while safe_current.is_set():
				await asyncio.sleep(5)
			# pin already set off, but set switch to off for mqtt update
			# to ensure it is not turned back on by mistake from mqtt
			self.trip_device.state.set_state("OFF")
			debug("tripped_handler: waiting for reset, relay off")
			while not self.trip_device.switch.value():
				await asyncio.sleep(.1)
			debug("Trip pin turned back on, safe_current is set")
			safe_current.set()

	async def amperage_handler(self):
		last_reading = 0
		self.amperage.publish.set()
		while True:
			reading = round(self.read_register(0x04) * self.k,3)
			if reading > self.threshold:
				self.trip_device.switch.off()
				safe_current.clear()
				error("Over current tripped! waiting for reset")
				self.trip_state.set_state("ON")
				await safe_current.wait()
				debug("Resuming current tracking/monitoring")
				self.trip_state.set_state("OFF")
				continue
			if abs(last_reading - reading) > self.diff:
				self.amperage.set_state(reading)
				last_reading = reading
			await asyncio.sleep_ms(100)