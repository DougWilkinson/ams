#vanity.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig (no hass_setup)

from machine import Pin
from neopixel import NeoPixel

# define the neopixels pin and count and clear
# using pin 2

leds = NeoPixel(Pin(2), 40)
leds.fill((0,0,0))
leds.write()

from ledmotion import LedMotion
from binary import Binary
from dhtx import DHTX
from dht import DHT22
from machine import Pin

# motion = Binary("bathroom_vanity_motion", pin=4, invert=False)
# led = LedMotion("bathroom_vanity", trigger=motion, led_pin=5, num_leds=40, on_seconds=180)

motion = Binary("bathroom_vanity_motion", pin=7, invert=False)

led = LedMotion("bathroom_vanity", leds, trigger=motion, off_delay=180)

temp = DHTX("vanity", DHT22(Pin(6)), poll_sec=60)

