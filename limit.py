# limit.py

version = (2,0,11)
# 2011: coverlimit class with superclass Cover

from machine import Pin
import time
from alog import info, error, debug, load_config, save_json
from device import Device
import uasyncio as asyncio
from hass import ha_setup
from cover import Cover

class CoverLimit(Cover):
	def __init__(self, name="coverlimit", 
				enable_pin=12, step_pin=13, dir_pin=15, 
				delay=1250, backoff_steps=300, max_steps=1000, 
				limit_pin=4, limit_pullup=0, invert_limit=False):
		super().__init__(name=name, 
				enable_pin=enable_pin, step_pin=step_pin, dir_pin=dir_pin, 
				delay=delay, backoff_steps=backoff_steps, max_steps=max_steps)
		self.limit_pin = Pin(limit_pin, limit_pullup) if limit_pin else None
		self.invert_limit = invert_limit
		asyncio.create_task(self.move())

	def at_limit(self):
		return not self.limit_pin.value() if self.invert_limit else self.limit_pin.value()

