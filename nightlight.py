# nightlight.py
# ledlight with option to turn on and off nightlight triggered by motion

from versions import versions
versions[__name__] = 13 
# 4: gradual on and off and motion trigger changed
# 5: fixed off task and led on/off tracking
# 10: support for webconfig (no hass_setup) fixed fade_on and fade_off
# 11: added fast_on to change values as they are adjusted
# 12: added switch to turn off nightlight triggered by motion 
#    (enabled if mqtt_connected event is not set for autonomous operation)
# 13: in progress - change from superclass to defined Light class
import time
from logger import info, debug, error
from system import start
from device import Device
import asyncio

from light import Light

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
class NightLight:
	def __init__(self, name, neopixels, trigger=None, off_delay=15) -> None:
		
		self.light = Light(name)
		self.leds = neopixels
		self.fade_on()
		self.fade_off()

		self.off_delay = off_delay
		self.motion = trigger.state
		self.last_motion = 0
		self.leds_on = asyncio.Event()

		self.nightlight = Device(f"{name}_nightlight", "ON", dtype="switch")

		if trigger:
			start(self.trigger_handler)
			start(self.delay_handler )

	def fade_off(self):
		self.fade(9,-1,-1)

	def fade_on(self):
		self.fade(0,10,1)

	def fast_on(self):
		self.fade(9,10,1)

	def fade(self, start, end, step, delay=0.05):
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
				self.fade_on()
				self.leds_on.set()
			else:
				info("set to brightness and rgb (already on, need to change to new values)")
				self.fast_on()
			return
		
		# otherwise any other command will turn off if leds are on
		if self.leds_on.is_set():
			info("set_state: turning off leds")
			self.fade_off()
			self.leds_on.clear()

	# def set_brightness(self, ev):
	# 	debug("bri ev: {}".format(ev))
	# 	# trigger rgb to update
	# 	self.s_bri.set_state(ev)

	# def set_color(self, ev):
	# 	debug("rgb ev: {}".format(ev))
	# 	# trigger led update
	# 	self.s_rgb.set_state(ev)

	async def delay_handler(self):
		while True:
			await asyncio.sleep(1)

			# only check for delay and turn off if nightlight switch is on
			# otherwise wait until switch state changes to check again
			if self.nightlight.state != "ON":
				await self.nightlight.needs_publishing.wait()
				continue

			if time.time() - self.last_motion < self.off_delay:
				continue

			if self.state.state == "ON":
				info("delay_handler: set_state called with: OFF")
				self.state.set_state("OFF")
			
			info("delay_handler: awaiting leds_on")
			await self.leds_on.wait()
			self.last_motion = time.time()

	async def trigger_handler(self):
		async for _ , ev in self.motion.q:
			
			# only turn on due to trigger event if nightlight switch is on
			if self.nightlight.state != "ON":
				continue

			if ev == "ON":
				self.last_motion = time.time()
				info("trigger_handler: state is: {}".format(self.state.state))
				if self.state.state == "OFF":
					info("trigger_handler: set_state called with: ON")
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