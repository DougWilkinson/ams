# sr04.py

# from versions import versions
# versions[__name__] = 1
# distance sensor SR-04

from machine import Pin, PWM
from time import sleep, ticks_us, sleep_us
# import uasyncio as asyncio
# from hass import ha_setup
# from device import Device
from core import info
import uasyncio as asyncio

# esp32-s2 led pins
# blue = 21
# green = 17
# red = 15 (used for motor on)

class SR04:
	def __init__(self, name, trig_pin, echo_pin, 
			  min_dist=5, max_dist=15,
			  green=17, blue=21) -> None:
		# self.dist = Device(name, "0", "mm", notifier_setup=ha_setup, publish=False)
		self.min = min_dist
		self.max = max_dist
		self.green = PWM(Pin(green), duty=0 )
		self.blue = PWM(Pin(blue), duty=0 )
		self.trig = Pin(trig_pin, Pin.OUT)
		self.echo = Pin(echo_pin, Pin.IN)
		self.samples = 0
		# asyncio.create_task(self.update())	

	async def wait_trigger(self,debug=False):
		in_range_count = 0

		self.green.duty(150)
		while in_range_count < 11:
			dist = self.sample()
			
			if dist > self.min and dist < self.max:
				in_range_count += 1
				if debug:
					info("dist = {}".format(dist))
			else:
				in_range_count = 0
				if debug:
					info("dist = {}".format(dist))
			await asyncio.sleep(.01)
			if not in_range_count:
				sleep_us(5000)

		self.green.duty(0)

	async def wait_clear(self, debug=False):
		out_range_count = 0

		self.blue.duty(150)
		while out_range_count < 11:
			dist = self.sample()
			
			if dist > self.min and dist < self.max:
				out_range_count = 0
				if debug:
					info("dist = {}".format(dist))
			else:
				out_range_count += 1
				if debug:
					info("dist = {}".format(dist))
			await asyncio.sleep(.01)
		self.blue.duty(0)

	def sample(self) -> int:
		self.trig.off()
		sleep_us(2)
		self.trig.on()
		sleep_us(10)
		self.trig.off()
		start_tick = ticks_us()
		end_tick = ticks_us()

		for i in range(20000):
			if self.echo.value():
				break
			start_tick = ticks_us()
					
		for i in range(20000):
			if not self.echo.value():
				break
			end_tick = ticks_us()
					
		return int( ( ( end_tick-start_tick ) * 0.034 ) / 2 )
