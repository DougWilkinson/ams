# dispenser.py

from time import time, sleep, sleep_us, sleep_ms
from machine import Pin
from alog import info, debug, started
from device import Device
from hass import Switch, Sensor
import asyncio

defaults = {"pd_sck": 14,
			"dout": 12,
			"update_sec": 1,
			"k": 229
			}

#@micropython.native
def toggle(p):
	p.value(1)
	p.value(0)

class Dispenser():
	
	def __init__(self, name, display=None, grams=34, motor_pin=5, hxclock_pin=12, hxdata_pin=14, k=263, fast=0.65, flick_ms=100 ):
		self.motor_pin = Pin(motor_pin, Pin.OUT)
		self.motor_pin.off()
		started(name)

		self.activate = Device(name + "/activate", "OFF", notifier=Switch)
		self.grams = Device(name + "/grams", state=45, notifier=Sensor)
		self.dispensed = Device(name + "/dispensed", state="0", notifier=Sensor)
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
		asyncio.create_task(self._grams(self.grams.setstate) )

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

	async def _grams(self, queue):
		async for _, msg in queue:
			info("dispenser: _grams")
			self.grams.state = int(msg)
			self.grams.publish.set()

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

	# .5 second average
	# reads 5 values and averages the 3 middle values
	def average(self):
		while len(self.values) < 5:
			for i in range(5):
				self.values.append(self.raw_read() )
				sleep_ms(100)
		new = self.raw_read()
		if new > 0:
			self.values.pop(0)
			self.values.append(new)
		self.sorted_vals = self.values.copy()
		self.sorted_vals.sort()
		print(self.sorted_vals)
		return sum(self.sorted_vals[1:-1])/3

	async def measure(self):
		self.values = []
		tare = self.average()
		target = self.grams.state + tare
		info("target: {} g".format(self.grams.state) )
		try:
			raw=tare
			self.motor_pin.on()
			last = 0
			same_count = 0
			
			# fast pace up to fast_percent of target
			for i in range(50):
				if (raw - tare) >= ( (target - tare) * self.fast_percent):
					break
				await asyncio.sleep_ms(100)
				raw = self.average()

				if raw <= last:
					same_count += 1
				else:
					same_count = 0

				# No change in hx, return error
				if raw-tare < -30:
					self.motor_pin.off()
					return int(raw-tare), "error - reset bin - "

				if raw < last:
					raw = last
				g = str( int( raw-tare ) )
				info("{} g".format(g) )
				if self.display:
					self.display.put( "state", g )
				last = raw

			# slow flicking pace
			for i in range(25):
				self.motor_pin.on()
				sleep_ms(self.flick_ms)
				self.motor_pin.off()			
				await asyncio.sleep(1)

				raw = self.average()
				if raw < last:
					raw = last
				if raw > target:
					raw = target
				g = str( int( raw-tare ) )
				info("{} g".format(g) )
				if self.display:
					self.display.put( "state", g )
					await asyncio.sleep(0)
				if raw >= target:
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
		return final, ""
