# rgbstatus.py

from versions import versions
versions[__name__] = 3

import time
from core import info, debug, started
from device import Device
from hass import ha_setup
import uasyncio as asyncio
from machine import Pin
from neopixel import NeoPixel

class RGBStatus:
	
	def __init__(self, name, pin=15, num_leds=3, brightness=15, min_brightness=5, urgent_ms=500,
			  glow_ms=1500):
		self.version = version
		self.leds = NeoPixel(Pin(pin), num_leds)
		self.setall()
		self.brightness = brightness
		self.min_brightness = min_brightness
		self.status = Device(name + "/rgbstatus", "unknown", notifier_setup=ha_setup)
		self.urgent_ms = urgent_ms
		self.glow_ms = glow_ms
		self.last = time.ticks_ms()
		asyncio.create_task(self.update())

	def setall(self, color=(0,0,0)):
		if self.leds is None:
			return
		self.leds.fill(color)
		self.leds.write()

	def get_pulse(self, max, use_min=False):
		min = self.min_brightness if use_min else 0
		pulse = time.ticks_diff(time.ticks_ms(),self.last)
		if pulse > max:
			pulse = max
			self.last = time.ticks_ms()
		# sweeps range of brightness (default 30)
		pulse = abs(int( (self.brightness*2) * (pulse/max) ) - self.brightness)
		pulse = min if pulse < min else pulse
		npulse = self.brightness - pulse
		npulse = min if npulse < min else npulse
		return pulse, npulse
	
	async def update(self, delay=5):
		# pulse = time.ticks_diff(time.ticks_ms(),self.last)
		# if pulse > self.flash_urgent_ms:
		# 	pulse = self.flash_urgent_ms
		# 	self.last = time.ticks_ms()
		# # sweeps range of brightness (default 30)
		# pulse = abs(int( (self.brightness*2) * (pulse/self.flash_urgent_ms) ) - self.brightness)
		# pulse = 0 if pulse < 0 else pulse
		# npulse = self.brightness - pulse
		# npulse = 0 if npulse < 0 else npulse
		# Purple pulse - Invalid/Init state
		laststate = ""
		while True:
			if "steady" not in self.status.state:
				self.leds.write()
			await asyncio.sleep_ms(delay)
			num_leds = len(self.leds)
			if laststate != self.status.state:
				if "steady" in self.status.state:
					self.setall((self.min_brightness,0,self.min_brightness))
				else:
					self.setall()
				laststate = self.status.state

			if self.status.state == "glow_one":
				pulse, npulse = self.get_pulse(self.glow_ms, use_min=True)
				color1 = (0,0,pulse)
				color2 = (0,0,pulse)
				num_leds = 1

			if self.status.state == "glow_two":
				pulse, npulse = self.get_pulse(self.glow_ms, use_min=True)
				color1 = (0,0,pulse)
				color2 = (0,0,pulse)
				num_leds = 2

			if self.status.state == "glow_purple":
				pulse, npulse = self.get_pulse(self.glow_ms, use_min=True)
				color1 = (pulse,0,pulse)
				color2 = (pulse,0,pulse)

			if self.status.state == "glow_green":
				pulse, npulse = self.get_pulse(self.glow_ms, use_min=True)
				color1 = (0,pulse,0)
				color2 = (0,pulse,0)
			
			if self.status.state == "pulse_red":
				pulse, npulse = self.get_pulse(self.urgent_ms)
				color1 = (pulse,0,0)
				color2 = (pulse,0,0)
			
			if self.status.state == "unknown":
				pulse, npulse = self.get_pulse(self.urgent_ms)
				color1 = (pulse >> 1,0,npulse >> 1)
				color2 = (npulse >> 1,0,pulse >> 1)
			
			for i in range(num_leds):
				if i % 2:
					self.leds[i] = color1
				else:
					self.leds[i] = color2

