# bed.py

from versions import versions
versions[__name__] = 1

from core import started, latch
from hx711 import HX711
from scale import Scale

# USB (side near dresser)
left_hx = hx=HX711(hxclock_pin=18, hxdata_pin=19, k=550, offset=0, samples=5)
left_bed = Scale("lbed/scale", hx, diff=30)

# main unit (near closet)
right_hx = hx=HX711(hxclock_pin=22, hxdata_pin=23, k=-1200, offset=0, samples=5)
right_bed = Scale("rbed/scale", hx, diff=30)

async def start(hostname):
	started(hostname)
	await latch.wait()
