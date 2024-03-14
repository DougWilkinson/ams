# hx711.py

from time import sleep, sleep_us
from machine import Pin

@micropython.native
def toggle(p):
	p.value(1)
	p.value(0)

class HX711():
	
	def __init__(self, hxclock_pin=12, hxdata_pin=14, k=386, offset=0 ):
		self.k = k
		self.offset = offset
		self.dataPin = Pin(hxdata_pin, Pin.IN)
		self.pdsckPin = Pin(hxclock_pin, Pin.OUT, value=0)
		# self.hx2g = 0.8075   # 0.8075
		self.powerup()
		self.rawvalue = 0
		self.sorted_vals = []
		self.values = []
		self.actual = 0

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
		return round(my/self.k + self.offset, 1)

