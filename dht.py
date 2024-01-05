# dht.py

version = (1, 0, 0)

from machine import Pin
import time
from alog import info, debug
from aconfig import setup, pubstate
import asyncio
import dht
from random import getrandbits

# For initial testing, not needed
class FakeDHT:
	def __init__(self) -> None:
		pass
	def temperature(self):
		return getrandbits(6)
	def humidity(self):
		return getrandbits(6)
	def	measure(self):
		pass

class Class:
	def __init__(self, name, settings):
		self.temp_name = name + "_temp"
		self.humidity_name = name + "_humidity"

		# Select right model in settings
		if '22' in name:
			# { "hass/sensor/name/dht22": { "module": "dht", "pin": 5, "poll_ms": 10000 } }
			self.dht = dht.DHT22(Pin(settings.get('pin') ))
		elif '11' in name:
			# { "hass/sensor/name/dht11": { "module": "dht"} }
			self.dht = dht.DHT11(Pin(settings.get('pin') ))
		else:
			# { "hass/sensor/name/dht": { "module": "dht"} }
			self.dht = FakeDHT()

		self.poll_ms = settings.get("poll_ms", 10000)
		
		# Start handler and haconfig for each entity
		# only one handler will be created (same name will de-dup)
		setup(name, self.handler, entity=self.temp_name, units="F")
		setup(name, self.handler, entity=self.humidity_name, units="%")
	
	# TODO: Fix error handling below, disabled to test with
	async def handler(self, event):
		while True:
			# readtemp
			# try:
			self.dht.measure()
			await pubstate(self.temp_name, round((self.dht.temperature() * 9 / 5) + 32,1))
			await pubstate(self.humidity_name, int(round(self.dht.humidity(),0) ) )
			await asyncio.sleep_ms(self.poll_ms)
			# except:
			# debug("dht: read error")
			# await asyncio.sleep(1)