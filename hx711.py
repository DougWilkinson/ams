# hx711.py
# async average updates
version = (2, 0, 0)

from time import sleep_ms, sleep_us
from machine import Pin
import uasyncio as asyncio

@micropython.native
def toggle(p):
	p.value(1)
	p.value(0)

class HX711():
	
	def __init__(self, hxclock_pin=12, hxdata_pin=14, k=386, offset=0, samples=3, min=-10000, max=10000 ):
		self.k = k
		self.offset = offset
		self.samples = samples
		self.min = min
		self.max = max
		self.dataPin = Pin(hxdata_pin, Pin.IN)
		self.pdsckPin = Pin(hxclock_pin, Pin.OUT, value=0)
		# self.hx2g = 0.8075   # 0.8075
		self.values = [0, ] * samples
		self.lower = False
		self.higher = False
		self.powerup()
		asyncio.create_task(self.update())

	def powerup(self):
		self.pdsckPin.value(0)
		self.powered = True
		sleep_ms(10)

	def isready(self):
		sleep_ms(1)
		return self.dataPin.value()

	# averages 3 values over 1 second
	def average(self):
		return round(sum(self.values)/ self.samples,1)
	
	def low(self):
		return self.lower
	
	def high(self):
		return self.higher

	# Update samples and low/high flags
	async def update(self):
		while True:
			# while not self.dataPin.value():
			# 	print(self.dataPin.value())
			# 	asyncio.sleep_ms(1)
			# sleep_us(10)
			raw = self.raw_read()
			if raw < 0 or raw > 1000:
				continue
			self.values.append(raw)
			self.values.pop(0)
			self.lower = True if self.average() < self.min else False
			self.higher = True if self.average() > self.max else False
			await asyncio.sleep_ms(300)

	def raw_read(self):
		# while not self.isready():
		# 	pass
		# sleep_us(10)
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
		return my/self.k + self.offset

