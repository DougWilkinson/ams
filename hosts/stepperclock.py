#stepperclock.py

from versions import versions
versions[__name__] = 1
# 1: new

import asyncio
from machine import Pin
from binary import Binary
from device import Device
from logger import info, debug
from time import sleep_us, ticks_ms
from localtime import offset_time
from system import start, exception_handler

index_pin = Pin(37, Pin.IN)

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

	def move_seconds(self, seconds):
		steps = seconds * 24
		if steps < 0:
			self.move_backward(-steps)
		else:
			self.move_forward(steps)

stepper_clock = Stepper(enable_pin=5, step_pin=7, dir_pin=9, on_delay_us=300, off_delay_us=300)

motion = Binary("stepper_clock_index", pin=index_pin, invert=False)

stepper_adjust = Device("stepper_clock_adjust_seconds", "")

@exception_handler
async def stepper_adjust_handler():
	info("stepper_adjust_handler: running")

	async for _, ev in stepper_adjust.q:
		
		if not ev:
			continue
		seconds = int(ev)
		if seconds == 0:
			continue
		debug(f"stepper_adjust: {seconds}")
		stepper_clock.move_seconds(seconds)
	
	stepper_adjust.set_state("0")

# clock_time = Device("stepper_clock_time", )

@exception_handler
async def advance_second_hand():
	info("advance_second_hand: running")
	last_second = offset_time()[5]
	stepper_clock.enable_pin.off()

	while True:
		second = offset_time()[5]
		if last_second == second:
			await asyncio.sleep(0.1)
			continue
		
		if second == 15:
			info(f"short move: 22 steps")
			stepper_clock.move_forward(23)
		else:
			stepper_clock.move_forward(24)
		last_second = second

start(advance_second_hand)

start(stepper_adjust_handler)
