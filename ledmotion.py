# ledlight.py

version = (2, 0, 4)
# 203: changed to trigger for lights on (any class with a state object)
# 204: ha_sub for _bri and _rgb

from machine import Pin
import time
from alog import info, debug, error
import uasyncio as asyncio
from neopixel import NeoPixel
from device import Device
from hass import ha_setup, ha_sub

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
class LedMotion:
	def __init__(self, name="ledmotion", led_pin=14, num_leds=3, trigger=None, on_seconds=15) -> None:

		self.state = Device(name, "OFF", dtype="light", notifier_setup=ha_setup)
		self.s_bri = Device("{}_bri".format(name), "10", dtype="light", notifier_setup=ha_sub)
		self.s_rgb = Device("{}_rgb".format(name), "0,255,255", dtype="light", notifier_setup=ha_sub)

		self.leds = NeoPixel(Pin(led_pin), num_leds)
		self.clear_leds()

		self.on_seconds = on_seconds
		self.motion = trigger.state
		self.motion_taskobj = None

		debug("ledlight: create tasks: {}".format(name) )
		asyncio.create_task(self.state_handler() )
		asyncio.create_task(self.bri_handler() )
		asyncio.create_task(self.rgb_handler() )
		if trigger:
			asyncio.create_task(self.motion_trigger() )

	def clear_leds(self):
		self.leds.fill((0,0,0))
		self.leds.write()

	def set_leds(self):
		bri = int(self.s_bri.state) / 255
		r, g, b = self.s_rgb.state.split(",")
		#bri = int(s_bri.state)/255
		rgb = (int( int(r) * bri), int( int(g) * bri), int(int(b) * bri) )
		self.leds.fill(rgb)
		self.leds.write()

	async def state_handler(self):
		async for _ , ev in self.state.q:
			debug("state ev: {}".format(ev))
			if "ON" in ev:
				debug("setting leds to {}/{}".format(self.s_bri.state, self.s_rgb.state))
				self.set_leds()
				continue
			self.clear_leds()

	async def bri_handler(self):
		async for _ , ev in self.s_bri.q:
			debug("bri ev: {}".format(ev))
			# trigger rgb to update
			self.state.set_state(self.state.state)

	async def rgb_handler(self):
		async for _ , ev in self.s_rgb.q:
			debug("rgb ev: {}".format(ev))
			# trigger led update
			self.state.set_state(self.state.state)

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
				self.state.set_state("ON")
