# lbed.py

# 2,0,0: 
version = (2, 0, 7)

import uasyncio as asyncio
from hx711 import HX711
from alog import started, info, latch
# notifier is hass
import hass
from device import Device

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces
hx=HX711(hxclock_pin=33, hxdata_pin=32, k=-229, max=300, offset=1420, samples=5)

scale = Device("lbed/scale", "0", "hx", notifier_setup=hass.ha_setup, publish=False)

async def start(hostname):
	started("lbed")
	diff = 30
	await asyncio.sleep(2)
	last = 0
	while True:
		current = hx.average()
		if abs(last - current) > diff:
			scale.set_state(current)
			last = current
		await asyncio.sleep(1)