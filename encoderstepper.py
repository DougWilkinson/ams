# encoderstepper.py

version = (2,0,11)
# 2011: cover encoder class with superclass Cover

from machine import Pin
import time
from alog import info, error, debug, load_config, save_json
from device import Device
import uasyncio as asyncio
from hass import ha_setup
from cover import Cover

class CoverEncoder(Cover):
	def __init__(self, name="coverencoder", 
				enable_pin=12, step_pin=13, dir_pin=15, 
				delay=1250, backoff_steps=300, max_steps=1000, 
				enc_pin=4, timeout_ms=5000):
		super().__init__(name=name, 
				enable_pin=enable_pin, step_pin=step_pin, dir_pin=dir_pin, 
				delay=delay, backoff_steps=backoff_steps, max_steps=max_steps)
		self.enc_pin = Pin(enc_pin)
		self.timeout = timeout_ms
		self.encoder_state = 0
		self.moved_steps = 0
		self.last_tick = time.ticks_ms()
		asyncio.create_task(self.move())

	def still_moving(self):
		diff = time.ticks_ms() - self.last_tick
		if diff > self.timeout:
			debug("stepper: move: timeout!")
			return False
		if self.encoder_state != self.enc_pin.value():
			debug("encoder: {}".format(diff) )
			self.last_tick = time.ticks_ms()
			self.encoder_state = self.enc_pin.value()
			self.moved_steps += self.encoder_state
		return True

	# disable this, moved_steps counts encoder changes above
	def increment_moved(self):
		pass
