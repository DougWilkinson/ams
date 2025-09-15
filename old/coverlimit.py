# coverlimit.py

from versions import versions
versions[__name__] = 3
# 2010: back to Class generated with chatgpt

from machine import Pin
import time
from core import info, error, debug, load_config, save_json
from device import Device
import asyncio
from hass import ha_setup

class CoverLimit:
	def __init__(self, name, enable_pin=12, step_pin=13, dir_pin=15, 
				 limit_pin=4, limit_pullup=0, invert_limit=False, 
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
		self.limit_pin = Pin(limit_pin, limit_pullup) if limit_pin else None
		self.invert_limit = invert_limit
		self.delay = delay
		self.backoff_steps = backoff_steps
		self.max_steps = max_steps

		asyncio.create_task(self.move())

	def onestep(self):
		self.step_pin.value(1)
		self.step_pin.value(0)
		time.sleep_us(self.delay)

	async def move(self):
		current_state = self.state.state
		debug("cover state: {}".format(self.state.state))
		async for _, ev in self.state.q:
			debug("current state: {} received {}".format(self.state.state, ev))
			if self.state.state == current_state:
				debug("cover: already in state {}".format(ev))
				continue

			debug("cover: {} -> {}".format(current_state, ev))
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
			moved = 0

			debug("moving: {} steps".format(self.max_steps))

			while not limit_reached and moved < self.max_steps:
				self.onestep()
				limit_reached = not self.limit_pin.value() if self.invert_limit else self.limit_pin.value()
				
				# don't count if homing
				if ev != "STOP":
					moved += 1

			if not limit_reached:
				self.enable_pin.value(1)
				save_json("cover.{}".format(self.state.name), {"state": ev})
				info("moved: Success and state saved!")
				continue
			
			debug("move: limit_reached: {}, moved: {}".format(limit_reached, moved))

			# Back off until limit not detected or backoff_steps reached
			self.dir_pin.value(not self.dir_pin.value())
			limit_reached = True
			moved = 0
			debug("move: limit reached, backing off {} steps".format(self.backoff_steps))
			while limit_reached and moved < self.backoff_steps:
				self.onestep()
				limit_reached = not self.limit_pin.value() if self.invert_limit else self.limit_pin.value()
				moved += 1

			self.enable_pin.value(1)
			debug("backoff: limit_reached: {}, moved: {}".format(limit_reached, moved))
			info("moved: State saved: CLOSE")
			save_json("cover.{}".format(self.state.name), {"state": "CLOSE"})
