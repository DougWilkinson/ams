#kitlight.py

from versions import versions
versions[__name__] = 11
# 11: converted to NightLightMotion

from machine import Pin
from neopixel import NeoPixel

# define the neopixels pin and count and clear
leds = NeoPixel(Pin(11), 40)
leds.fill((0,0,0))
leds.write()

#from ledmotion import LedMotion
from nightlightmotion import NightLightMotion

from binary import Binary

motion = Binary("kitchen_cabinet_motion", pin=13, invert=False)
led = NightLightMotion("kitchen_cabinet", leds, trigger=motion, off_delay=180)

