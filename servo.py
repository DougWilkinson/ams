#servo.py
# class for controlling SG90 type servos
# freq=50Hz, duty between 20-130

from versions import versions
versions[__name__] = 1
# 1: new

import asyncio
from machine import Pin, PWM
from device import Device
from logger import info, debug
from system import exception_handler, start

class Servo():
	def __init__(self, name, pin=5, init_pos="", min=20, max=130, save_state=False):
		
		# set initial position if desired or leave duty at 0 (off)
		if init_pos:
			needs_publishing = True
			init_duty=int(init_pos)
		else:
			needs_publishing = False
			init_duty=0

		self.position = Device(f"{name}_position", init_pos, save_state=save_state, needs_publishing=needs_publishing )
		self.pin = Pin(pin)
		self.min = min
		self.max = max
		self.servo = PWM(self.pin, freq=50, duty=init_duty)
		self.current_position = init_duty

		start(self.handle_position)
	
	# set absolute position
	def set(self, pos):
		pos = max(min(pos, self.max), self.min)
		self.position.set_value(pos)

	# set position based on percentage
	def setp(self, percentage):
		pos = int((self.max - self.min) * percentage / 100)
		self.set_position(pos)

	@exception_handler
	async def handle_position(self):
		info(f"handle_position: {self.position.name}: running")
		await asyncio.sleep(0.3)
		self.servo.duty(0)
		
		async for _ , ev in self.position.q:
			self.current_position = int(float(ev))

			self.servo.duty(self.current_position)
			debug(f"handle_position: {self.position.name}: {self.current_position}")

			await asyncio.sleep(0.3)
			self.servo.duty(0)
