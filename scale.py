# scale.py

from versions import versions
versions[__name__] = 6
# 5: new standard for device and hass
# 6: set last value to compare to 0 instead of -100 so first value published is real and not a 0
import asyncio
from device import Device
from time import time
from logger import info, error
from system import exception_handler

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces

class Scale():
	def __init__(self, name, hx, diff) -> None:
		self.scale = Device(name, "0", "hx", )
		asyncio.create_task(self.update(hx, diff))	
	
	@exception_handler
	async def update(self, hx, diff):
		info(f"scale: starting: {self.scale.name}"  )
		await asyncio.sleep(2)
		last = 0
		last_pub = time()
		while True:
			current = hx.average()
			if abs(last - current) > diff or time() - last_pub > 300:
				info("{}: values: {}".format(self.scale.name, hx.values) )
				self.scale.set_state(current)
				last = current
				last_pub = time()
			await asyncio.sleep(1)
