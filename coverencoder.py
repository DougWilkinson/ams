#stepper.py

version = (1, 0, 0)
# async version

from machine import Pin
import time
from alog import info, error, debug
from device import Device
import asyncio
from main import load_config
from hass import ha_setup

class CoverEncoder:
	def __init__(self, name, enable_pin=12, step_pin=13, dir_pin=15, 
				 enc_pin=4, limit_pin=4, limit_pullup=0, invert_limit=False, 
				 timeout=5000, delay=1250, backoff_steps=0, max_steps=1000):
		try:
			state = load_config("cover.saved")
		except:
			state = {'state': 'closed', 'position': 0}
		
		self.state = Device(name, state['state'], dtype="cover", notifier_setup=ha_setup)
		self.enable_pin = Pin(enable_pin, Pin.OUT)
		self.dir_pin = Pin(dir_pin, Pin.OUT)
		self.step_pin = Pin(step_pin, Pin.OUT)
		self.enc_pin = Pin(enc_pin, Pin.IN)
		self.timeout = timeout
		self.last_tick = time.ticks_ms()
		self.encoder_state = 0
		self.limit_pin = Pin(limit_pin, limit_pullup) if limit_pin else None
		self.invert_limit = invert_limit
		self.backoff_steps = backoff_steps
		self.delay = delay
		self.pos = -1
		self.max_steps = max_steps
		self.direction = -1

		self.stop()
		asyncio.create_task(self._activate(self.state.set_state))

	def onestep(self):
		self.step_pin.value(1)
		self.step_pin.value(0)
		time.sleep_us(self.delay)

	def at_limit(self):
		return not self.limit_pin.value() if self.invert_limit else self.limit_pin.value()

	def start(self, direction):
		self.last_tick = time.ticks_ms()
		self.encoder_state = self.enc_pin.value()
		self.dir_pin.value(direction)
		if self.at_limit():
			self.backoff()
		self.enable_pin.value(0)

	def stop(self):
		self.enable_pin.value(1)

	def still_moving(self):
		if self.encoder_state != self.enc_pin.value():
			self.last_tick = time.ticks_ms()
			self.encoder_state = self.enc_pin.value()
		if time.ticks_ms() - self.last_tick > self.timeout:
			debug("stepper: move: timeout!")
			return False
		return True

	def backoff(self):
		time.sleep_ms(100)
		moved = 0
		info("stepper: home: limit detected, backing off")
		self.start(1)
		while self.at_limit() and self.still_moving():
			self.onestep()
			moved += 1
		if self.at_limit():
			error("backoff: timeout during backoff, still at_limit")
			self.stop()
			self.state.state = "jammed"
			self.state.publish = True
			return False

		info("backoff: remaining: {}".format(self.backoff_steps - moved))
		self.start(1)
		while self.backoff_steps > moved:
			self.onestep()
			moved += 1

		self.stop()
		return True

	def home(self):
		info("stepper: homing")
		self.start(0)

		while self.still_moving() and not self.at_limit():
			self.onestep()

		self.stop()

		if not self.backoff():
			return False

		self.pos = 0
		self.state.state = "closed"
		self.state.publish = True
		return True

	def set_state_status(self, status="working"):
		if self.pos == 0:
			self.state.state = status
			self.state.publish.set()
			if self.pos == 0:
				self.state.state = "closed"
			else:
				self.state.state = "open"
			self.state.publish.set()

	async def _activate(self, queue):
		async for _, msg in queue:
			info("dispenser: _activate:")
			
			if "open" == msg:
				newsteps = self.max_steps
			elif "closed" == msg:
				newsteps = 0
			else:
				continue
			
			if self.pos < 0 or newsteps == self.pos:
				self.pos = newsteps
				self.set_state_status()
				continue
			
			if newsteps > self.pos:
				step = 1
				self.start(1)
			else:
				step = -1
				self.start(0)

			debug("open: moving to: {}".format(newsteps))
			while (self.pos != newsteps) and self.still_moving() and not self.at_limit():
				self.onestep()
				self.pos += step
			
			self.stop()
			if newsteps != self.pos:
				error("stepper: Move failed at position: {}".format(self.pos))
				self.set_state_status(status='jammed')
			else:
				self.set_state_status()
