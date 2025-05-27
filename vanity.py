#vanity.py

version = (2, 0, 0)

from core import info, latch
from ledmotion import LedMotion
from binary import Binary
import dhtx
from dht import DHT22
from machine import Pin

# motion = Binary("bathroom_vanity_motion", pin=4, invert=False)
# led = LedMotion("bathroom_vanity", trigger=motion, led_pin=5, num_leds=40, on_seconds=180)

motion = Binary("bathroom_vanity_motion", pin=36, invert=False)

led = LedMotion("bathroom_vanity", trigger=motion, led_pin=38, num_leds=40, on_seconds=180)

temp = dhtx.init("vanity", DHT22(Pin(40)), poll_sec=60)

async def start(hostname):
		await latch.wait()

