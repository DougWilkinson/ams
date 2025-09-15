# lbed.py

from versions import versions
versions[__name__] = 3

from core import started, latch
from hx711 import HX711
from scale import Scale

hx = hx=HX711(hxclock_pin=14, hxdata_pin=12, k=229, offset=0, samples=5)
leftbed = Scale("lbed/scale", hx, diff=30)

async def start(hostname):
	started(hostname)
	await latch.wait()
