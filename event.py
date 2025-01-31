# event.py
# takes a trigger and target
# optional delay to turn target off

from versions import versions
versions[__name__] = 1


import time
from core import info, debug
import uasyncio as asyncio
from device import Device

class Event:
	def __init__(self, trigger: Device, target: Device, off_delay=0) -> None:
		self.last_triggered = -1
		asyncio.create_task(self.trigger_handler(trigger, target, off_delay) )

	async def trigger_handler(self, trigger, target, off_delay):

		async for _, event in trigger.q:
			debug("{} - {}".format(trigger.name, event))
		
			if event == "ON":
				if target.state == "OFF":
					self.last_triggered = time.time()
					if off_delay:
						asyncio.create_task(self.delay_handler(target, off_delay) )
					target.on()
				else:
					debug("retriggered on")
					self.last_triggered = time.time()

			if event == "OFF" and target.state == "ON":
				debug("trigger off")
				if not off_delay:
					target.off()

	# async def delay_handler(self, target, off_delay):
	# 	while True:
	# 		if self.last_triggered > 0 and time.time() - self.last_triggered > off_delay:
	# 			debug("event: target delay off")
	# 			target.off()
	# 		await asyncio.sleep(1)
	async def delay_handler(self, target, off_delay):
		passed = 0
		while passed < off_delay:
			await asyncio.sleep(off_delay - passed)
			passed = time.time() - self.last_triggered

		target.off()
