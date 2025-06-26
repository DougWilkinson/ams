# ledlite.py
# a smaller version of ledlight

from versions import versions
versions[__name__] = 3
# 203: changed to trigger for lights on (any class with a state object)
# 204: ha_sub for _bri and _rgb

from machine import Pin
import time
from core import info, debug, error
import asyncio
from neopixel import NeoPixel

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
class LedMotion:
	def __init__(self, name="ledmotion", led_pin=14, num_leds=3, trigger=None, on_seconds=15, rgb=(0,10,10) ) -> None:

		self.rgb = rgb
		self.leds = NeoPixel(Pin(led_pin), num_leds)
		self.clear_leds()

		self.on_seconds = on_seconds
		self.motion = trigger.state
		self.motion_taskobj = None

		debug("ledlight: create tasks: {}".format(name) )
		if trigger:
			asyncio.create_task(self.motion_trigger() )

	def clear_leds(self):
		self.leds.fill((0,0,0))
		self.leds.write()

	def set_leds(self):
		self.leds.fill(self.rgb)
		self.leds.write()

	async def off_task(self):
		try:
			await asyncio.sleep(self.on_seconds)
			self.clear_leds()
		except asyncio.CancelledError:	
			info("off_task cancelled")
		except Exception as e:
			error("unknown error: {}".format(e))
		self.motion_taskobj = None

	async def motion_trigger(self):
		async for _ , ev in self.motion.q:
			if ev == "ON":
				while self.motion_taskobj:
					debug("canceling previous off_task {}".format(self.motion_taskobj))
					self.motion_taskobj.cancel()
					await asyncio.sleep(1)
				self.motion_taskobj = asyncio.create_task(self.off_task())
				debug("leds on, off_task started {}".format(self.motion_taskobj))
				self.set_leds()