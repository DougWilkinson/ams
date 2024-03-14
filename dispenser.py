# dispenser.py

# 1,0,3 - fixed last = raw placement
version = (1,0,3)

from time import time, sleep, sleep_us, sleep_ms, ticks_us
from machine import Pin
from alog import info, debug, started
from device import Device
from hass import ha_setup
import asyncio

class Dispenser():

	def is_on(self):
		return True
	def is_off(self):
		return False

	def __init__(self, name, display=None, cycles=3, tray=None, motor_pin=5, hx_read=None ):
		self.motor_pin = Pin(motor_pin, Pin.OUT)
		self.motor_pin.off()
		started(name)

		self.activate = Device(name + "/activate", "OFF", dtype="switch", notifier=ha_setup)
		self.cycles = Device(name + "/cycles", state=cycles, dtype="sensor", notifier=ha_setup)
		self.dispensed = Device(name + "/dispensed", state=0, units="g", ro=True, dtype="sensor", notifier=ha_setup)
		# set this event to signal "not busy dispensing"
		self.dispensed.event.set()

		self.hx_read = hx_read
		if tray:
			self.tray = tray
		else:
			self.tray = self
		self.flick_ms = 50
		self.rawvalue = 0
		self.sorted_vals = []
		self.values = [0, ] * 3
		self.actual = 0
		# flag set when something changes
		self.error = ""
		self.display = display
		# start waiting for state changes
		asyncio.create_task(self._activate(self.activate.setstate) )
		asyncio.create_task(self._cycles(self.cycles.setstate) )

	async def _activate(self, queue):
		async for _, msg in queue:
			info("dispenser: _activate:")
			if "ON" != msg:
				continue
			if self.tray.is_off():
				continue
			self.activate.event.set()
			self.actual, self.error = await self.measure()
			self.dispensed.state = self.actual
			self.dispensed.publish.set()
			self.activate.event.clear()
			self.dispensed.event.set()
			# Update state at end of dispense to OFF
			self.activate.publish.set()
			if self.error:
				self.display.put("state", "err - {} g - ".format(self.actual) )

	async def _cycles(self, queue):
		async for _, msg in queue:
			info("dispenser: _cycles")
			self.cycles.state = int(msg)
			self.cycles.publish.set()

	# averages 3 values over 1 second
	def average(self):
		for i in range(3):
			self.values[i] = self.hx_read()
			sleep_ms(300)
		return sum(self.values)/3

	async def measure(self, grams=17, flick=100, waitsec=2):
		#info("target: {} cycles".format(self.cycles.state) )
		rgrams = 0
		try:
			tare = self.average()
			raw = tare
			last = tare
			low_count = 0
			
			# flick until cycles seen or bin is full
			while low_count < 12 and raw - tare < grams and self.tray.is_on():
				self.motor_pin.on()
				if (raw-tare) / grams >= 0.8:
					sleep_ms(flick)
					self.motor_pin.off()			
					await asyncio.sleep(waitsec)
					info("{} / {} / {}".format(raw, last, raw-last) )
					if raw - last < .3:
						low_count += 1
					else:
						low_count = 0
					last = raw

				raw = self.average()
				rgrams = round( raw-tare,1 )
				info("{} / {} / {}".format(rgrams, grams, low_count) )
							
			# while raw - tare < grams and self.tray.is_on():
			# 	self.motor_pin.on()
			# 	sleep_ms(flick)
			# 	self.motor_pin.off()			
			# 	await asyncio.sleep(waitsec)
			# 	raw = self.average()
			# 	rgrams = round( raw-tare,1 )
			# 	info("{} / {}".format(rgrams, grams) )
			# 	# if raw < last:
			# 	# 	raw = last
				
			# 	last = raw

			self.motor_pin.off()
		except:
			self.motor_pin.off()
		if self.display:
			self.display.put( "state", int(rgrams) )
			await asyncio.sleep(0)
		return str(rgrams), ""
