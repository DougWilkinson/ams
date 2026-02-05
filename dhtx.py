# dhtx.py

from versions import versions
versions[__name__] = 11
# 10: using webconfig and no ha_setup (switched back to class based)
# 11: added debug

from system import start
from logger import debug, info, error
from device import Device
import asyncio

class DHTX:
	def __init__(self, name, dht, poll_sec=60):
		self.dht = dht
		self.name = name
		self.poll_sec = poll_sec
		self.temp = Device(name + "_temp", "0", "F" )
		self.humidity = Device(name + "_humidity", "0", "%" )
	
		start(self.dhtx_handler)
	
	async def dhtx_handler(self):
		info("dhtx_handler for: {} - running".format(self.name) )
		while True:
			# readtemp
			for i in range(4):
				try:
					self.dht.measure()
					self.temp.set_state( round( (self.dht.temperature() * 9 / 5) + 32,1) )
					self.humidity.set_state(int(round(self.dht.humidity(),0) ) )
					debug("dht: {} temp: {} humidity: {}".format(self.name, self.temp.state, self.humidity.state) )
					break
				except OSError:
					error("dht: {} read timeout".format(self.temp.name) )
					await asyncio.sleep(2)
		
			await asyncio.sleep(self.poll_sec)
