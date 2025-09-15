#workbench.py

from versions import versions
versions[__name__] = 4

from core import latch, hostname
#from ledclock import LEDClock
from presence import Presence

#from neopixel import NeoPixel
import asyncio

detector = Presence(hostname)

async def start(hostname):
	await latch.wait()

