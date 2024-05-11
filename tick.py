# tick.py
# measure ticks between gpio on state
# start/stop to correct time

version = (2,0,0)
# async version

from device import Device
from machine import Pin, PWM
from time import ticks_us, sleep, time, ticks_diff
from alog import error, debug
from hass import ha_setup
import uasyncio as asyncio

ticks = []
last_tick = 0
ticked = asyncio.ThreadSafeFlag()

clock_running = asyncio.Event()
clock_stopped = asyncio.Event()

async def init(name, tick_pin=34, pause_pin=14, samples=60):

	# do first to stop random pwm motion
	pause_pwm = PWM(Pin(pause_pin), freq=50, duty=47)
	pause_pwm.freq(1)
	pause_pwm.duty(0)

	# Set from HA when correction needed
	pause_seconds = Device(name + "_pause_seconds", "0", units="seconds", notifier_setup=ha_setup )

	# don't publish before measuring
	tick_seconds = Device(name + "_ticktime", "0", units="seconds", notifier_setup=ha_setup, publish=False)

	# Do not publish state until known
	clock_state = Device(name, "OFF", dtype="binary_sensor", notifier_setup=ha_setup, publish=False)

	tick_pin = Pin(tick_pin, Pin.IN)
	tick_pin.irq(trigger=Pin.IRQ_FALLING, handler=tick_cb)

	asyncio.create_task(pause_handler(pause_pwm, pause_seconds))
	asyncio.create_task(state_handler(clock_state))
	asyncio.create_task(tick_handler(tick_seconds, samples))

# publishes tick time average and maintains list of ticks
# Sets clock_running Event based on timeout waiting for ticks
async def tick_handler(tick_seconds,samples):
	global clock_running
	global clock_stopped
	global ticked
	global ticks
	while True:
		try:
			await asyncio.wait_for(ticked.wait(), 5)
			ticks.clear()
			for i in range(samples):
				await asyncio.wait_for(ticked.wait(), 5)
				clock_running.set()
				clock_stopped.clear()
			if len(ticks) > samples:
				ticks.sort()
				ticks.pop(0)
				ticks.pop()
			average = sum(ticks) / len(ticks)
			tick_seconds.set_state(round(average/1000000, 4) )
		except asyncio.TimeoutError:
			debug("state: clock stopped tick lost 5 seconds:")
			clock_running.clear()
			clock_stopped.set()

async def setpwm(pause_pwm, duty=47) -> int:
	pause_pwm.duty(duty)
	pause_pwm.freq(50)
	debug("tick:setpwm: {}".format(duty))
	await asyncio.sleep(1)
	return duty

async def pause_handler(pause_pwm, pause_seconds):
	currentpwm = 47
	sleep(1)
	pause_start = 0
	async for _, value in pause_seconds.q:
		seconds = int(value)
		if int(seconds) < 60:
			continue
		# adjust pause time for stop/start delays
		seconds = seconds - 35
		# stop clock
		for step in range(currentpwm, 71):
			currentpwm = await setpwm(pause_pwm, step)
		# shut off pwm
		pause_pwm.freq(1)
		pause_pwm.duty(0)

		try:
			await asyncio.wait_for(clock_stopped.wait(), 10)
		except asyncio.TimeoutError:
			error("pause: clock did not stop!" )
			currentpwm = await setpwm(pause_pwm, 47)
			# -1 means did not stop
			pause_seconds.set_state(-1)
			continue

		error("pause: clock stopped, waiting {} seconds".format(seconds))
		# Wait for correction
		await asyncio.sleep(seconds)

		error("pause: Restarting clock")
		# start clock (swing to 92 and let go!)
		for step in range(currentpwm, 93):
			currentpwm = await setpwm(pause_pwm, step)
		# let go!
		currentpwm = await setpwm(pause_pwm, 47)
		# shut off pwm
		pause_pwm.freq(1)
		pause_pwm.duty(0)

		# wait for clock to restart
		try:
			await asyncio.wait_for(clock_running.wait(), 10)
		except asyncio.TimeoutError:
			error("pause: clock did not restart!" )
			currentpwm = await setpwm(pause_pwm, 47)
			# -2 means did not restart
			pause_seconds.set_state(-2)

		# set back to 0 to signal success
		pause_seconds.set_state(0)

# clock state is ON or OFF (binary sensor)
async def state_handler(clock_state):
	global clock_running
	global clock_stopped
	await asyncio.sleep(20)
	while True:
		await clock_running.wait()
		clock_state.set_state("ON")
		await clock_stopped.wait()
		clock_state.set_state("OFF")

# Adds tick diffs to list only
def tick_cb(irq):
	global last_tick
	global ticks
	global ticked
	tick = ticks_us()
	ticks.append(ticks_diff(tick, last_tick))
	last_tick = tick
	ticked.set()
