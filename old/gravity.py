# gravity.py

from versions import versions
versions[__name__] = 1
# 4: gradual on and off and motion trigger changed
# 5: fixed off task and led on/off tracking

from machine import Pin
import time
import asyncio
from neopixel import NeoPixel
#from device import Device
#from hass import ha_setup, ha_sub
from light import Light
from core import info
import random
import math

class Gravity(Light):
	def __init__(self, name="gravity", led_pin=14, num_leds=20, trigger=None) -> None:
		super().__init__(name=name)

		self.leds = NeoPixel(Pin(led_pin), num_leds)
		self.clear_leds()

		self.motion = trigger.state
		self.last_motion = 0
		self.leds_on = asyncio.Event()

		self.speeds = [0] * num_leds
		self.
		info("gravity: create tasks: {}".format(name) )


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

	def random_color(self):
		return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

	def random_brightness(self):
		return random.uniform(0.1, 1.0)

	def random_speed(self):
		return random.uniform(0.1, 2.0)

	async def animate(self):
		num_leds = self.leds.n
		color = self.random_color()
		brightness = self.random_brightness()
		speed = self.random_speed()
		gravity = 0.1  # adjust to taste
		friction = 0.95  # adjust to taste

		angle = 0
		velocity = speed
		while True:
			# calculate new angle based on velocity and gravity
			angle += velocity
			velocity *= friction
			velocity -= gravity * math.sin(math.radians(angle))

			# map angle to LED position
			led_index = int((angle % 360) / 360 * num_leds)

			# set LED color and brightness
			self.leds[led_index] = (int(color[0] * brightness), int(color[1] * brightness), int(color[2] * brightness))
			self.leds.write()

			# slow down as velocity decreases
			await asyncio.sleep(0.05 / (velocity + 0.1))

			# stop animation when velocity is close to zero
			if abs(velocity) < 0.01:
				break
