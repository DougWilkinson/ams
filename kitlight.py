#kitlight.py

from versions import versions
versions[__name__] = 3

from core import info, latch
from ledmotion import LedMotion
from binary import Binary

motion = Binary("kitchen_cabinet_motion", pin=4, invert=False)
led = LedMotion("kitchen_cabinet", trigger=motion, led_pin=5, num_leds=40, on_seconds=180)

async def start(hostname):
		await latch.wait()

