# ledlight.py

# Think about not using classes, call an "init" function that create_tasks for:
# motion, rgb, bri and state that define the Device and maintains that device?
# cleaner? But won't be able to see "state" when in repl? Does that matter?

from machine import Pin
import time
from core import info, debug
import asyncio
from neopixel import NeoPixel
from device import Device
from hass import ha_setup

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
class LEDLight:
	def __init__(self, name, led_pin, num_leds=3, motion_pin=None, on_secs=300) -> None:
		self.state = Device(name, "OFF", dtype="light", notifier_setup=ha_setup)
		self.s_bri = Device("/{}_bri".format(name), "10", notifier_setup=ha_setup)
		self.bri = int(self.s_bri) / 255
		self.s_rgb = Device("/{}_rgb".format(name), "0,255,255", dtype="light", notifier_setup=ha_setup)
		self.rgb = tuple(self.rgb.state.split(",") )
		self.leds = NeoPixel(led_pin, num_leds)
		self.setall()
		self.motion_pin = Pin(motion_pin, Pin.IN)
		self.motion = Device("/{}_motion".format(name), "OFF", dtype="binary_sensor", notifier_setup=ha_setup)
		debug("ledlight: create tasks: {}".format(name) )
		asyncio.create_task(self.state_handler() )
		asyncio.create_task(self.bri_handler() )
		asyncio.create_task(self.rgb_handler() )

	def setall(self, color=(0,0,0)):
		if self.leds is None:
			return
		self.leds.fill(color)
		self.leds.write()

	async def state_handler(self):
		async for ev in self.state.q:
			if ev == "ON":
				self.leds.setall(self.rgb)
				continue
			self.leds.setall()

	async def bri_handler(self):
		async for ev in self.s_bri.q:
			self.bri = int(self.s_bri.state) / 255
			self.state.set_state(self.state.state)

	async def rgb_handler(self, name):
		async for ev in self.s_rgb.q:
			r, g, b = ev.split(",") 
			self.rgb = (int( int(r) * self.bri), int( int(g) * self.bri), int(int(b) * self.bri) )
			self.state.set_state(self.state.state)

	async def motion_handler(self, name):
		last_motion = time.time()
		while True:
			if self.motion_pin.value():
				self.in_motion = True
				self.last_motion = time.time()
			if self.in_motion and time.time() - self.last_motion
							
class OutEvent:
	def __init__(self, name, *settings) -> None:
		self.name = name
		pin_num = settings.get('pin', None)
		if not pin_num:
			raise ValueError
		self.pin = Pin(pin_num, Pin.IN)
		self.invert = settings.get('invert', 1) > 0		# default False
		#self.inbus_event = inbus_event
		debug("task create: {}".format(name))
		tasklist[name] = asyncio.create_task(self.handler())
		self.last = self.read_pin()

	async def handler(self):
		while True:
			new = (not self.pin.value()) if self.invert else (self.pin.value() > 0)
			if new != self.last:
				outbus[self.name] = "ON" if new else "OFF"
				outbus_event.set()
			

class Class:
	
	def __init__(self, instance="ledlight.ledlight"):
		config = load_file()[instance]		
		self.instance = instance
		self.version = version
		for i in config.keys():
			defaults[i] = config[i]
		name = instance.split('.')[1]
		if defaults['leds'] > 0:
			self.leds = NeoPixel(Pin(defaults['pin']), defaults["leds"])
			self.setall()
		else:
			self.leds = None
		self.light_rgb = (0,0,0)
		self.light_name = defaults['light_name']
		self.night_rgb = tuple([int(i) for i in defaults['night_rgb'].split(",")])
		self.night_name = defaults['night_name']
		self.motion_name = defaults['motion_name']
		self.last_motion = time()
		self.night_on = False
		self.night_delay = defaults['night_delay']

	def setall(self, color=(0,0,0)):
		if self.leds is None:
			return
		self.leds.fill(color)
		self.leds.write()

	def update(self):
		changed = False
		# change nightlight color only
		if self.night_name in eventbus and self.night_rgb != eventbus[self.night_name]:
			self.night_rgb = eventbus[self.night_name]
			changed = True
		# motion turn on nightlight or change color
		if self.motion_name in eventbus:
			self.last_motion = time()
			if self.light_rgb == (0,0,0):
				if not self.night_on or (changed and self.night_on):
					self.night_on = True
					self.setall(self.night_rgb)
		# Turn off nightlight after delay
		if self.night_on and time() - self.last_motion > self.night_delay:
			self.night_on = False
			self.setall()
		# set light, turn off nightlight
		if self.light_name in eventbus and self.light_rgb != eventbus[self.light_name]:
			self.light_rgb = eventbus[self.light_name]
			self.setall(self.light_rgb)
			self.night_on = False
