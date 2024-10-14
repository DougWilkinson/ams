# tick.py
# measure ticks between gpio on state
# start/stop to correct time

from versions import versions
versions[__name__] = 3

from device import Device
from machine import Pin, PWM
from time import ticks_us, sleep, time, ticks_diff
from core import error, debug
from hass import ha_setup
import uasyncio as asyncio

class Tick:
	def __init__(self, name, tick_pin=5, pause_pin=14, samples=60):

		self.ticks = []
		self.last_tick = 0
		self.ticked = asyncio.ThreadSafeFlag()

		self.clock_running = asyncio.Event()
		self.clock_stopped = asyncio.Event()

		# do first to stop random pwm motion
		self.pause_pwm = PWM(Pin(pause_pin), freq=50, duty=47)
		#self.pause_pwm.freq(1)
		#self.pause_pwm.duty(0)

		# Set from HA when correction needed
		self.pause_seconds = Device(name + "_pause", "0", units="seconds", notifier_setup=ha_setup )

		# don't publish before measuring
		self.tick_seconds = Device(name + "_ticktime", "0", units="seconds", notifier_setup=ha_setup, publish=False)

		# Do not publish state until known
		self.clock_state = Device(name, "OFF", dtype="binary_sensor", notifier_setup=ha_setup, publish=False)

		self.tick_pin = Pin(tick_pin, Pin.IN)
		self.tick_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.tick_cb)
		self.samples = samples

		asyncio.create_task(self.pause_handler())
		asyncio.create_task(self.state_handler())
		asyncio.create_task(self.tick_handler())

# publishes tick time average and maintains list of ticks
# Sets clock_running Event based on timeout waiting for ticks
	async def tick_handler(self):
		while True:
			try:
				await asyncio.wait_for(self.ticked.wait(), 5)
				self.ticks.clear()
				for i in range(self.samples):
					await asyncio.wait_for(self.ticked.wait(), 5)
					self.clock_running.set()
					self.clock_stopped.clear()
				if len(self.ticks) > self.samples:
					self.ticks.sort()
					self.ticks.pop(0)
					self.ticks.pop()
				average = sum(self.ticks) / len(self.ticks)
				self.tick_seconds.set_state(round(average/1000000, 4) )
			except asyncio.TimeoutError:
				debug("state: clock stopped tick lost 5 seconds:")
				self.clock_running.clear()
				self.clock_stopped.set()

	async def setpwm(self, duty=47) -> int:
		self.pause_pwm.duty(duty)
		self.pause_pwm.freq(50)
		debug("tick:setpwm: {}".format(duty))
		await asyncio.sleep(1)
		return duty

	async def pause_handler(self):
		currentpwm = 47
		sleep(1)
		pause_start = 0
		async for _, value in self.pause_seconds.q:
			seconds = int(value)
			if int(seconds) < 60:
				continue
			# adjust pause time for stop/start delays
			seconds = seconds - 35
			# stop clock
			for step in range(currentpwm, 71):
				currentpwm = await self.setpwm(step)
			# shut off pwm
			self.pause_pwm.freq(1)
			self.pause_pwm.duty(0)

			try:
				await asyncio.wait_for(self.clock_stopped.wait(), 10)
			except asyncio.TimeoutError:
				error("pause: clock did not stop!" )
				currentpwm = await self.setpwm(47)
				# -1 means did not stop
				self.pause_seconds.set_state(-1)
				continue

			error("pause: clock stopped, waiting {} seconds".format(seconds))
			# Wait for correction
			await asyncio.sleep(seconds)

			error("pause: Restarting clock")
			# start clock (swing to 92 and let go!)
			for step in range(currentpwm, 93):
				currentpwm = await self.setpwm(step)
			# let go!
			currentpwm = await self.setpwm(47)
			# shut off pwm
			self.pause_pwm.freq(1)
			self.pause_pwm.duty(0)

			# wait for clock to restart
			try:
				await asyncio.wait_for(self.clock_running.wait(), 10)
			except asyncio.TimeoutError:
				error("pause: clock did not restart!" )
				currentpwm = await self.setpwm(47)
				# -2 means did not restart
				self.pause_seconds.set_state(-2)

			# set back to 0 to signal success
			self.pause_seconds.set_state(0)

	# clock state is ON or OFF (binary sensor)
	async def state_handler(self):
		await asyncio.sleep(20)
		while True:
			await self.clock_running.wait()
			self.clock_state.set_state("ON")
			await self.clock_stopped.wait()
			self.clock_state.set_state("OFF")

	# Adds tick diffs to list only
	def tick_cb(self, irq):
		global last_tick
		global ticks
		global ticked
		tick = ticks_us()
		self.ticks.append(ticks_diff(tick, self.last_tick))
		self.last_tick = tick
		self.ticked.set()
