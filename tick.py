# tick.py
# measure ticks between gpio on state
# start/stop to correct time

from versions import versions
versions[__name__] = 10
# 10: support for webconfig (no ha_setup) - also removed pause functionality

from device import Device
from machine import Pin
from time import ticks_us, sleep, time, ticks_diff
from logger import error, info
from system import start
import asyncio

class Tick:
	def __init__(self, name, tick_pin=5, samples=60):

		self.ticks = []
		self.last_tick = 0
		self.ticked = asyncio.ThreadSafeFlag()

		self.clock_running = asyncio.Event()
		self.clock_stopped = asyncio.Event()

		# don't publish before measuring
		self.tick_seconds = Device(name + "_ticktime", "0", units="seconds")

		# Do not publish state until known
		self.clock_state = Device(name, "OFF", dtype="binary_sensor")

		self.tick_pin = Pin(tick_pin, Pin.IN)
		self.tick_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.tick_cb)
		self.samples = samples

		start(self.tick_handler)

# publishes tick time average and maintains list of ticks
# Sets clock_running Event based on timeout waiting for ticks
	async def tick_handler(self):
		info("tick_handler: running")
		while True:
			try:
				await asyncio.wait_for(self.ticked.wait(), 5)
				self.ticks.clear()
				info(f"tick_handler: sampling {self.samples} ticks " )
				for i in range(self.samples):
					await asyncio.wait_for(self.ticked.wait(), 5)
					if not self.clock_running.is_set():
						self.clock_running.set()
						self.clock_stopped.clear()
						self.clock_state.set_state("ON")
				if len(self.ticks) > self.samples:
					self.ticks.sort()
					self.ticks.pop(0)
					self.ticks.pop()
				average = sum(self.ticks) / len(self.ticks)
				self.tick_seconds.set_state(round(average/1000000, 4) )

			except asyncio.TimeoutError:
				error("tick: timeout: 5 seconds - waiting for next tick")
				self.clock_running.clear()
				self.clock_stopped.set()
				self.clock_state.set_state("OFF")
				# wait until we see another tick before resuming sampling
				await asyncio.wait_for(self.ticked.wait())

	# Adds tick diffs to list only
	def tick_cb(self, irq):
		tick = ticks_us()
		self.ticks.append(ticks_diff(tick, self.last_tick))
		self.last_tick = tick
		self.ticked.set()
