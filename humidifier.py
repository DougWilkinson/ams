# humidifier.py

version = (2, 0, 0)
# 208: broke into scale.py and this file

from core import info, latch
from hx711 import HX711
from scale import Scale

hx = HX711(hxclock_pin=18, hxdata_pin=19, k=229, max=1000, offset=1450, samples=5)
testbed = Scale("humidifier_water", hx, diff=10)

async def start(hostname):
	await latch.wait()