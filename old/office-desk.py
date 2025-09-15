#office-desk.py

from versions import versions
versions[__name__] = 1
# 1: fixed u prefix and upgrade to 1.25 micropython

from core import latch, hostname
from presence import Presence

#from neopixel import NeoPixel
import asyncio

detector = Presence(hostname)

async def start(hostname):
	await latch.wait()

