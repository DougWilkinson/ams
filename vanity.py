#vanity.py

version = (2, 0, 0)

from core import info, latch
from ledmotion import LedMotion
from binary import Binary

motion = Binary("bathroom_vanity_motion", pin=4, invert=False)
led = LedMotion("bathroom_vanity", trigger=motion, led_pin=5, num_leds=40, on_seconds=180)

async def start(hostname):
		await latch.wait()

