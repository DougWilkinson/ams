# pwmstatus.py

from versions import versions
versions[__name__] = 10
# 10: converted to new standard

import time
import asyncio
from machine import Pin, PWM

class PWMStatus:
	
	def __init__(self, pin=15, brightness=15, min_brightness=5, glow_ms=1500):
		self.led = PWM(Pin(pin), freq=1000, duty=0)
		self.brightness = brightness
		self.min_brightness = min_brightness
		self.glow_ms = glow_ms
		self.last = time.ticks_ms()

		self.pulse_on = asyncio.Event()

		asyncio.create_task(self.update())

	def on(self):
		self.pulse_on.set()
	
	def off(self):
		self.led.duty(0)
		self.pulse_on.clear()

	def get_pulse(self, max, use_min=False):
		min = self.min_brightness if use_min else 0
		pulse = time.ticks_diff(time.ticks_ms(),self.last)
		if pulse > max:
			pulse = max
			self.last = time.ticks_ms()
		# sweeps range of brightness (default 30)
		pulse = abs(int( (self.brightness*2) * (pulse/max) ) - self.brightness)
		pulse = min if pulse < min else pulse
		return pulse
	
	async def update(self, delay=5):

		laststate = ""

		while True:
			await self.pulse_on.wait()

			pulse = self.get_pulse(self.glow_ms, use_min=True)
			self.led.duty(pulse)

			await asyncio.sleep_ms(delay)
		