#toyclock.py

from versions import versions
versions[__name__] = 14
# 10: converted to webconfig (no hass_setup)
# 11: add binary support for motion detection and dht22
# 12: added blinkled dimming and no invert on/off
# 13: added stepper clock function
# 14: fixed issue with waiting without sleeping (caused second hand led to be messed up)

from ledclock import LEDClock
from binary import Binary
from dht import DHT22
from machine import Pin
from dhtx import DHTX
from blinkled import on_led
from time import sleep_us
from system import start, exception_handler
from device import Device
from logger import info, debug, error
from localtime import offset_time
import asyncio

# dim status led
on_led[0] = (0,0,5)

clock = LEDClock("toyclock", pin=11, num_leds=13, 
		hand_index=[6,7,8,9,10,11,0,1,2,3,4,5,12],
		direction_index=[1,-1,1,-1,1,-1,-1,1,-1,1,-1,1],
		edge_index=[6,7,8,9,10,11,0,1,2,3,4,5,12],
		min_hand_length=1, hour_hand_length=1, tail_length=0,
		face_rgb=(1,1,1), hand_rgb=(25,25,25) )

motion = Binary("bedroom_motion", pin=12, invert=False)

minute_index = Binary("bedroom_minute_index", pin=9, invert=False)

dht = DHTX("bedroom", DHT22(Pin(8)), poll_sec=60)

class Stepper:
	def __init__(self, enable_pin=5, step_pin=7, dir_pin=9, on_delay_us=300, off_delay_us=300):
		self.enable_pin = Pin(enable_pin, Pin.OUT)
		self.enable_pin.on()
		self.dir_pin = Pin(dir_pin, Pin.OUT)
		self.dir_pin.off()
		self.step_pin = Pin(step_pin, Pin.OUT)
		self.step_pin.off()
		self.on_delay_us = on_delay_us
		self.off_delay_us = off_delay_us

		# low is normal step, high is 1/4 step
		self.ms2_pin = Pin(2, Pin.OUT)
		self.ms2_pin.on()


	def move(self, steps):
		for i in range(steps):
			self.step_pin.on()
			sleep_us(self.on_delay_us)
			self.step_pin.off()
			sleep_us(self.off_delay_us)

	def move_forward(self, steps):
		self.dir_pin.on()
		self.move(steps)

	def move_backward(self, steps):
		self.dir_pin.off()
		self.move(steps)

	def move_steps(self, steps):
		if steps < 0:
			self.move_backward(-steps)
		else:
			self.move_forward(steps)

	def move_seconds(self, seconds):
		steps = seconds * 24
		if steps < 0:
			self.move_backward(-steps)
		else:
			self.move_forward(steps)

stepper_clock = Stepper(enable_pin=1, step_pin=3, dir_pin=4, on_delay_us=0, off_delay_us=3250)

stepper_adjust = Device("toyclock_adjust_steps", "")

@exception_handler
async def stepper_adjust_handler():
	info("stepper_adjust_handler: running")

	async for _, ev in stepper_adjust.q:
		
		if not ev:
			continue
		steps = int(ev)
		if steps == 0:
			continue

		stepper_clock.enable_pin.off()
		debug(f"stepper_adjust: {steps}")
		stepper_clock.move_steps(steps)
		stepper_clock.enable_pin.on()
	
	stepper_adjust.set_state("0")

# clock_time = Device("stepper_clock_time", )

@exception_handler
async def advance_five_seconds():
	info("advance_second_hand: running")
	last_second = offset_time()[5]

	while True:
		second = offset_time()[5]
		
		# wait for next 5th second
		if (last_second == second) or (second % 5 != 0):
			await asyncio.sleep(.5)
			continue
		
		stepper_clock.enable_pin.off()
		if second == 55:
			stepper_clock.move_forward(15)
		else:
			stepper_clock.move_forward(11)
		last_second = second
		stepper_clock.enable_pin.on()

start(advance_five_seconds)

start(stepper_adjust_handler)

