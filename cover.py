# cover.py

version = (2,0,11)
# 2011: Super class for limit and encoder

from machine import Pin
import time
from alog import info, error, debug, load_config, save_json
from device import Device
import uasyncio as asyncio
from hass import ha_setup

class Cover:
	def __init__(self, name="cover", enable_pin=12, step_pin=13, dir_pin=15, 
				 delay=1250, backoff_steps=300, max_steps=1000):
		try:
			state = load_config("cover.{}".format(name))
		except:
			state = {'state': 'CLOSE', 'position': 0}

		self.state = Device(name, state['state'], dtype="cover", notifier_setup=ha_setup, set_lower=True)
		self.enable_pin = Pin(enable_pin, Pin.OUT)
		self.enable_pin.value(1)
		self.dir_pin = Pin(dir_pin, Pin.OUT)
		self.step_pin = Pin(step_pin, Pin.OUT)
		self.limit_pin = None
		self.invert_limit = False
		self.delay = delay
		self.backoff_steps = backoff_steps
		self.max_steps = max_steps
		self.moved_steps = 0
		#used for encoder timeout, must be reset on each move
		self.last_tick = time.ticks_ms()

	def onestep(self):
		self.step_pin.value(1)
		self.step_pin.value(0)
		time.sleep_us(self.delay)
	
	def at_limit(self):
		return False

	def still_moving(self) -> bool:
		return True
	
	def increment_moved(self):
		self.moved_steps += 1

	async def move(self):
		current_state = self.state.state
		debug("cover state: {}".format(self.state.state))
		async for _, ev in self.state.q:
			debug("cover: {} -> {}".format(current_state, ev))
			if self.state.state == current_state:
				continue

			current_state = self.state.state

			if current_state == "OPEN":
				self.state.set_state("open")
			else:
				self.state.set_state("closed")

			# Move to open or close max_steps
			# open direction is 1 or True
			self.dir_pin.value("OPEN" in ev)
			self.enable_pin.value(0)

			limit_reached = False
			self.moved_steps = 0
			self.last_tick = time.ticks_ms()

			debug("moving: {} steps".format(self.max_steps))

			while not self.at_limit() and self.still_moving() and self.moved_steps < self.max_steps:
				self.onestep()
				
				# don't count if homing
				if ev != "STOP":
					self.increment_moved()

			if self.at_limit():
				debug("limit_reached: moved: {} steps, backoff: {}".format(self.moved_steps, self.backoff_steps))
				
				# reverse direction
				self.dir_pin.value(not self.dir_pin.value())
				self.moved_steps = 0

				# move until not at limit anymore
				while self.at_limit() and self.moved_steps < self.backoff_steps:
					self.onestep()
					self.increment_moved()

			self.enable_pin.value(1)
			info("moved: State saved: {}".format(ev))
			save_json("cover.{}".format(self.state.name), {"state": ev} )
