# testbed.py

version = (2, 0, 9)
# 208: broke into scale.py and this file

from alog import started, info, latch
from hx711 import HX711
from scale import Scale

hx = hx=HX711(hxclock_pin=32, hxdata_pin=33, k=229, max=300, offset=1407, samples=5)
testbed = Scale("testbed_scale", hx, diff=20)

async def start(hostname):
	started(hostname)
	await latch.wait()