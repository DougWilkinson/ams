# scale.py

version = (2, 0, 8)
# 208: fixed name

import uasyncio as asyncio
from hass import ha_setup
from device import Device

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces

class Scale():
	def __init__(self, name, hx, diff) -> None:
		scale = Device(name, "0", "hx", notifier_setup=ha_setup, publish=False)
		asyncio.create_task(self.update(scale, hx, diff))	
	
	async def update(self, scale, hx, diff):
		await asyncio.sleep(2)
		last = -100
		while True:
			current = hx.average()
			if abs(last - current) > diff:
				print(hx.values)
				scale.set_state(current)
				last = current
			await asyncio.sleep(1)
