# dispenser.py

from time import time, sleep, sleep_us, sleep_ms
from machine import Pin
from alog import info, debug, started
from device import Device
from hass import ha_setup
import asyncio

#@micropython.native
def toggle(p):
	p.value(1)
	p.value(0)

class Dispenser():
	
	def __init__(self, name, display=None, cycles=3, motor_pin=5, hxclock_pin=12, hxdata_pin=14, k=263, fast=0.65, flick_ms=50 ):
		self.motor_pin = Pin(motor_pin, Pin.OUT)
		self.motor_pin.off()
		started(name)

		self.activate = Device(name + "/activate", "OFF", dtype="switch", notifier=ha_setup)
		self.cycles = Device(name + "/cycles", state=cycles, dtype="sensor", notifier=ha_setup)
		self.dispensed = Device(name + "/dispensed", state=0, units="g", ro=True, dtype="sensor", notifier=ha_setup)
		# set this event to signal "not busy dispensing"
		self.dispensed.event.set()

		self.k = k
		self.dataPin = Pin(hxdata_pin, Pin.IN)
		self.pdsckPin = Pin(hxclock_pin, Pin.OUT, value=0)
		self.gain = 128
		# self.hx2g = 0.8075   # 0.8075
		self.powerup()
		self.fast_percent = fast
		self.flick_ms = flick_ms
		self.rawvalue = 0
		self.sorted_vals = []
		self.values = []
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
			if "ON" == msg:
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

	def powerup(self):
		self.pdsckPin.value(0)
		self.powered = True

	def isready(self):
		sleep(.001)
		return self.dataPin.value()

	def raw_read(self):
		while not self.isready():
			pass
		sleep_us(10)
		my = 0
		for idx in range(24):
			toggle(self.pdsckPin)
			data = self.dataPin.value()
			if not idx:
				neg = data
			else:
				my = ( my << 1) | data
		toggle(self.pdsckPin)
		if neg: my = my - (1<<23)
		return round(my/self.k, 1)

	# 
	# averages last and current
	def average(self):
		while len(self.values) < 3:
			for i in range(3):
				self.values.append(self.raw_read() )
				sleep_ms(100)
		new = self.raw_read()
		if new > 0:
			self.values.pop(0)
			self.values.append(new)
			self.slope = int((self.values[2] - self.values[0])/3)
		# print(self.values)
		# print("slope: ", self.slope)
		return sum(self.values[-2:])/2

	async def measure(self):
		info("target: {} cycles".format(self.cycles.state) )
		try:
			self.values = []
			tare = self.average()
			raw = tare
			last = tare
			zero_slope_count = 0
			cycles = 0
			
			# flick until cycles seen or bin is full
			while zero_slope_count < 20:
				self.motor_pin.on()
				sleep_ms(self.flick_ms)
				self.motor_pin.off()			
				await asyncio.sleep(1)

				raw = self.average()
				if raw < last:
					raw = last
				g = str( int( raw-tare ) )

				info("g: {} sv: {} zc: {} sc: {}".format(g, self.slope, zero_slope_count, cycles) )
				
				# count a zero slope
				if self.slope == 0:
					zero_slope_count += 1
				else:
					zero_slope_count = 0
				# cound one slope if == 8
				if zero_slope_count == 8:
					if self.display:
						self.display.put( "state", g )
						self.dispensed.state = int(raw-tare)
						self.dispensed.publish.set()
						await asyncio.sleep(0)
					cycles +=1
					if cycles == self.cycles.state:
						info("cycles reached")
						break
				last = raw

			self.motor_pin.off()
		except:
			self.motor_pin.off()
		final = self.average()
		g = str( int( final-tare ) )
		info("final: {} g".format(g) )
		if self.display:
			self.display.put( "state", g )
			await asyncio.sleep(0)
		return g, ""
