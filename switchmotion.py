# switchmotion.py

version = (2, 0, 4)

from machine import Pin
import time
from alog import info, debug, error
import uasyncio as asyncio
from device import Device
from hass import ha_setup

class SwitchMotion:
	def __init__(self, name="switchmotion", switch_pin=13, trigger=None, on_seconds=5) -> None:

		self.state = Device(name, "OFF", dtype="switch", notifier_setup=ha_setup)
		self.switch = Pin(switch_pin, Pin.OUT)
		self.switch.off()

		self.on_seconds = on_seconds
		#self.motion_taskobj = None
		self.retrigger = False
		self.remaining_secs = 0
		self.waiting = False

		debug("switchmotion: create tasks: {}".format(name) )
		asyncio.create_task(self.state_handler() )
		if trigger:
			self.motion = trigger.state
			asyncio.create_task(self.motion_trigger() )

	async def state_handler(self):
		async for _ , ev in self.state.q:
			debug("state ev: {}".format(ev))
			if "ON" in ev:
				debug("switch: ON")
				self.switch.on()
				continue
			self.switch.off()

	async def off_task(self):
		self.waiting = True
		while self.retrigger or self.remaining_secs > 0:
			if self.retrigger:
				debug("retrigger!")
				self.remaining_secs = self.on_seconds
				self.retrigger = False
			await asyncio.sleep(5)
			self.remaining_secs -= 5
		debug("off_task ending: retrigger: {}, remaining: {}".format(self.retrigger, self.remaining_secs))
		self.switch.off()
		self.state.set_state("OFF")
		self.waiting = False

	# async def off_task(self):
	# 	try:
	# 		await asyncio.sleep(self.on_seconds)
	# 		self.switch.off()
	# 	except asyncio.CancelledError:	
	# 		info("off_task cancelled")
	# 	except Exception as e:
	# 		error("unknown error: {}".format(e))
	# 	self.motion_taskobj = None

	async def motion_trigger(self):
		async for _ , ev in self.motion.q:
			if ev == "ON":
				self.retrigger = True
				if self.waiting:
					debug("trigger: already in waiting off_task")
					continue
				debug("trigger: off_task created")
				asyncio.create_task(self.off_task())
				# while self.motion_taskobj:
				# 	debug("canceling previous off_task {}".format(self.motion_taskobj))
				# 	self.motion_taskobj.cancel()
				# 	await asyncio.sleep(1)
				# self.motion_taskobj = asyncio.create_task(self.off_task())
				# debug("switch on, off_task started {}".format(self.motion_taskobj))
				self.state.set_state("ON")
