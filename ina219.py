# ina219.py

version = (2,0,8)
import uasyncio as asyncio
from machine import Pin
from device import Device
from hass import ha_setup
from alog import error, debug

safe_current = asyncio.Event()
safe_current.set()

# i2c object defined (required)
# trip_pin: pin to turn off when trip_threshold_amps exceeded
# trip_threshold_amps: value to exceed to shutoff trip pin object 
# diff: minimum value for updates
# k: multiplier for Ampere conversion
class INA219:
	def __init__(self, name, i2c, trip_pin_obj, trip_threshold_amps=0.9, diff=0.05, k=0.0000214292):
		self.i2c = i2c
		self.address = 0x40
		self.write_register(0x05, 16793)
		self.write_register(0, 2463)
		self.k = k
		self.diff = diff
		self.amperage = Device(name, "0.0", units="A", notifier_setup=ha_setup)
		self.threshold = trip_threshold_amps
		
		# trip Pin object (GPIO to relay or transistor)
		self.trip_pin = trip_pin_obj

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
			while not self.trip_pin.value():
				await asyncio.sleep(.1)
			debug("Trip pin turned back on, safe_current is set")
			safe_current.set()

	async def amperage_handler(self):
		last_reading = 0
		self.amperage.publish = True
		while True:
			reading = round(self.read_register(0x04) * self.k,3)
			if reading > self.threshold:
				self.trip_pin.off()
				safe_current.clear()
				error("Over current tripped! waiting for reset")
				self.trip_state.set_state("ON")
				await asyncio.wait_for(safe_current)
				debug("Resuming current tracking/monitoring")
				self.trip_state.set_state("OFF")
				continue
			if abs(last_reading - reading) > self.diff:
				self.amperage.set_state(reading)
				last_reading = reading
			await asyncio.sleep(.1)