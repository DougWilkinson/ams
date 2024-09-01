# scale.py

from versions import versions
versions[__name__] = 3
# 209: added periodic publish and self.scale

import uasyncio as asyncio
from hass import ha_setup
from device import Device
from time import time

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces

class Scale():
	def __init__(self, name, hx, diff) -> None:
		self.scale = Device(name, "0", "hx", notifier_setup=ha_setup, publish=False)
		asyncio.create_task(self.update(hx, diff))	
	
	async def update(self, hx, diff):
		await asyncio.sleep(2)
		last = -100
		last_pub = time()
		while True:
			current = hx.average()
			if abs(last - current) > diff or time() - last_pub > 300:
				print(hx.values)
				self.scale.set_state(current)
				last = current
				last_pub = time()
			await asyncio.sleep(1)
