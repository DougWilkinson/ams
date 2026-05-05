# hx711a.py

from versions import versions
versions[__name__] = 10
# 6: added rate_ms (default 300) should be able to take 10 reads per second at lowest rate
# 7: added min/max average and tare
# 8: added start and exception handler
# 9: removed rounding from average values
# 10: changed average and how values are updated to replace near ones with averages

from time import sleep_ms
from machine import Pin
import asyncio

from logger import info, debug, error
from system import start, exception_handler

def toggle(p):
	p.value(1)
	p.value(0)

class HX711():
	
	def __init__(self, hxclock_pin=12, hxdata_pin=14, 
			  k=386, offset=0, samples=3, rate_ms=300,
			  min=-10000, max=10000, diff=5, discard=0 ):
		self.k = k
		self.offset = offset
		self.samples = samples

		# used to track first set of reads
		self.raw_read_count = 0
		
		# delay between readings
		self.rate_ms = rate_ms

		# number of samples to discard on min/max after sorting
		self.discard = discard

		# amount the last average has to change before returning a new average
		self.diff = diff

		# min/max values after adjusting k and offset
		self.min = min
		self.max = max

		self.dataPin = Pin(hxdata_pin, Pin.IN)
		self.pdsckPin = Pin(hxclock_pin, Pin.OUT, value=0)
		# self.hx2g = 0.8075   # 0.8075
		self.values = [0, ] * samples
		self.tare = 0
		self.powerup()
		start(self.update_samples)

	def powerup(self):
		self.pdsckPin.value(0)
		self.powered = True
		sleep_ms(10)

	def isready(self):
		sleep_ms(1)
		return self.dataPin.value()

	# averages 3 values over 1 second
	def average(self):

		if self.raw_read_count < len(self.values):
			debug(f"hx711: init: self.values: {self.values}")
			return 0

		#debug(f"hx711: self.values: {self.values}")
		
		# if not discarding, return average
		if not self.discard:
			current_average = sum(self.values)/ len(self.values)
		else:
			# if discarding, return average of remaining values
			newcopy = self.values.copy()
			newcopy.sort()
			newcopy = newcopy[self.discard:-self.discard]
			#debug(f"hx711: after discard: {newcopy}")
			current_average = sum(newcopy)/ len(newcopy)
			
		return current_average - self.tare
	
	def set_tare(self):
		self.tare = 0
		self.tare = self.average()

	# Update samples and low/high flags
	@exception_handler
	async def update_samples(self):
		values_length = len(self.values)
		last_raw = self.raw_read()

		while True:
			raw = self.raw_read()
			#debug(f"hx711: raw: {raw}")

			if self.min == 0 and raw > -self.diff and raw < 0:
				raw = 0

			# if they are the same sign, delta_raw is abs difference
			delta_raw = abs(last_raw - raw)

			# check for different signs to get difference
			if raw < 0 and last_raw > 0:
				delta_raw = last_raw + raw
			
			if raw > 0 and last_raw < 0:
				delta_raw = raw + last_raw
		
			# If new value is near last value, replace with current average instead
			if delta_raw < self.diff:
				raw = self.average() + self.tare

			if raw >= self.min and raw < self.max:
				self.raw_read_count += 1
				self.values.append(raw)
				self.values.pop(0)

			last_raw = raw
			await asyncio.sleep_ms(self.rate_ms)

	def raw_read(self):
		# while not self.isready():
		# 	pass
		# sleep_us(10)
		my = 0
		# d = disable_irq()
		for idx in range(24):
			toggle(self.pdsckPin)
			data = self.dataPin.value()
			if not idx:
				neg = data
			else:
				my = ( my << 1) | data
		# one read = gain of 128
		toggle(self.pdsckPin)
		# enable_irq(d)
		if neg: my = my - (1<<23)
		return (my - self.offset)/self.k

