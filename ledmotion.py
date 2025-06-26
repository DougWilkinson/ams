# ledlight.py

from versions import versions
versions[__name__] = 5
# 4: gradual on and off and motion trigger changed
# 5: fixed off task and led on/off tracking

from machine import Pin
import time
from core import info, debug, error
import asyncio
from neopixel import NeoPixel
from device import Device
from hass import ha_setup, ha_sub
from light import Light

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
class LedMotion(Light):
	def __init__(self, name="ledmotion", led_pin=14, num_leds=3, trigger=None, on_seconds=15) -> None:
		super().__init__(name=name)

		self.leds = NeoPixel(Pin(led_pin), num_leds)
		self.clear_leds()

		self.on_seconds = on_seconds
		self.motion = trigger.state
		self.last_motion = 0
		self.leds_on = asyncio.Event()

		debug("ledlight: create tasks: {}".format(name) )
		if trigger:
			asyncio.create_task(self.motion_trigger() )
			asyncio.create_task(self.off_task() )

	def clear_leds(self):
		self.set_leds(9,-1,-1)

	def set_leds(self, start=0, end=10, step=1, delay=0.05):
		#info("set_leds: start: {}, end: {}, step: {}, delay: {}".format(start, end, step, delay))
		max_bri = int(self.s_bri.state) / 255
		r, g, b = self.s_rgb.state.split(",")
		#bri = int(s_bri.state)/255
		for i in range(start, end, step):
			bri = max_bri * i / 9
			rgb = (int( int(r) * bri), int( int(g) * bri), int(int(b) * bri) )
			self.leds.fill(rgb)
			self.leds.write()
			time.sleep(delay)

	
	def set_state(self, ev):
		if "ON" in ev:
			# only turn on if not already on
			if not self.leds_on.is_set():
				info("set_state: turning on leds to {}/{}".format(self.s_bri.state, self.s_rgb.state))
				self.set_leds()
				self.leds_on.set()
			return
		
		# otherwise any other command will turn off if leds are on
		if self.leds_on.is_set():
			info("set_state: turning off leds")
			self.clear_leds()
			self.leds_on.clear()

	# def set_brightness(self, ev):
	# 	debug("bri ev: {}".format(ev))
	# 	# trigger rgb to update
	# 	self.s_bri.set_state(ev)

	# def set_color(self, ev):
	# 	debug("rgb ev: {}".format(ev))
	# 	# trigger led update
	# 	self.s_rgb.set_state(ev)

	async def off_task(self):
		while True:
			await asyncio.sleep(1)

			if time.time() - self.last_motion < self.on_seconds:
				continue

			if self.state.state == "ON":
				info("off_task: set_state called with: OFF")
				self.state.set_state("OFF")
			
			info("off_task: awaiting leds_on")
			await self.leds_on.wait()
			self.last_motion = time.time()

	async def motion_trigger(self):
		async for _ , ev in self.motion.q:
			if ev == "ON":
				self.last_motion = time.time()
				info("motion_trigger: state is: {}".format(self.state.state))
				if self.state.state == "OFF":
					info("motion_trigger: set_state called with: ON")
					self.state.set_state("ON")

"""
21:36:25: 2019168: kitlight: kitchen_cabinet_motion: on
21:36:25: 2018832: kitlight: motion_trigger: state is: ON
21:36:25: 2018352: kitlight: pubstate: kitchen_cabinet_motion, ON, pubflag: True
21:36:25: 2017680: kitlight: pub: topic: hass/binary_sensor/kitchen_cabinet_motion/state
21:36:26: 2014064: kitlight: state ev: ON
21:36:26: 2013776: kitlight: state: ON bri: 36 rgb: 0,255,255
21:36:26: 2013456: kitlight: setting leds to 36/0,255,255
21:36:26: 2012944: kitlight: set_leds: start: 0, end: 10, step: 1, delay: 0.05
21:36:26: 2011280: kitlight: pub: topic: hass/light/kitchen_cabinet/state
21:36:30: 2011728: kitlight: kitchen_cabinet_motion: off
21:36:30: 2011184: kitlight: pubstate: kitchen_cabinet_motion, OFF, pubflag: True
21:36:30: 2010512: kitlight: pub: topic: hass/binary_sensor/kitchen_cabinet_motion/state
21:36:33: 2018784: kitlight: kitchen_cabinet_motion: on
21:36:33: 2018448: kitlight: motion_trigger: state is: ON
21:36:33: 2017968: kitlight: pubstate: kitchen_cabinet_motion, ON, pubflag: True
21:36:33: 2017296: kitlight: pub: topic: hass/binary_sensor/kitchen_cabinet_motion/state
21:36:33: 2015696: kitlight: state ev: ON
21:36:33: 2015408: kitlight: state: ON bri: 36 rgb: 0,255,255
21:36:33: 2015088: kitlight: setting leds to 36/0,255,255
21:36:33: 2014576: kitlight: set_leds: start: 0, end: 10, step: 1, delay: 0.05
21:36:34: 2012912: kitlight: pub: topic: hass/light/kitchen_cabinet/state
21:36:37: 2020032: kitlight: kitchen_cabinet_motion: off
21:36:37: 2019488: kitlight: pubstate: kitchen_cabinet_motion, OFF, pubflag: True
21:36:37: 2018816: kitlight: pub: topic: hass/binary_sensor/kitchen_cabinet_motion/state
"""