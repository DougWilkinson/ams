# coverstepper.py

version = (2,0,0)
# stop = home, non-class version, moved load/save to alog
# save to cover.name


from machine import Pin
import time
from core import info, error, debug, load_config, save_json
from device import Device
import asyncio
from hass import ha_setup

# state states are: "open" and "closed"
# state set values are "OPEN", "STOP" and "CLOSE"
# Save the "set" state to flash, not the "state" which is lower case
# want to compare any new set state to last needs to use the set value

# after taking action, set state to corresponding state (STOP is ignored)
# "OPEN" -> "open", "STOP" -> None, "CLOSE" -> "closed"
# set values must be lower case for HA to recognize them
# delay is 1250 for 8BY stepper,??? for NEMA?

def init(name, enable_pin=12, step_pin=13, dir_pin=15, 
			limit_pin=4, limit_pullup=0, invert_limit=False, 
			delay=1250, backoff_steps=300, max_steps=1000):
	try:
		state = load_config("cover.{}".format(name))
	except:
		state = {'state': 'CLOSE', 'position': 0 }
	
	state = Device(name, state['state'], dtype="cover", 
				notifier_setup=ha_setup, set_lower=True)
	enable_pin = Pin(enable_pin, Pin.OUT)
	enable_pin.value(1)
	dir_pin = Pin(dir_pin, Pin.OUT)
	step_pin = Pin(step_pin, Pin.OUT)
	
	limit_pin = Pin(limit_pin, limit_pullup) if limit_pin else None
	invert_limit = invert_limit

	asyncio.create_task(move_cover(state, enable_pin, dir_pin, step_pin, limit_pin,
			invert_limit, delay, backoff_steps, max_steps) )

def onestep(step_pin, delay):
	step_pin.value(1)
	pass
	step_pin.value(0)
	time.sleep_us(delay)

async def move_cover(state, enable_pin, dir_pin, step_pin, limit_pin,
			invert_limit=False, delay=1250, backoff_steps=0, max_steps=1000):
	
	current_state = state.state
	debug("cover state: {}".format(state.state))
	async for _, ev in state.q:
		debug("cover: received {}".format(ev))
		if state.state == current_state:
			debug("cover: already in state {}".format(ev))
			continue

		debug("cover: {} -> {}".format(current_state, ev))
		current_state = state.state

		if current_state == "OPEN":
			state.set_state("open")
		else:
			state.set_state("closed")

		# Move to open or close max_steps
		dir_pin.value("OPEN" in ev)
		enable_pin.value(0)
		if ev == "STOP":
			dir_pin.value(0)
		limit_reached = False
		moved = 0
		debug("moving: {} steps".format(max_steps))	
		while not limit_reached and moved < max_steps:
			onestep(step_pin, delay)
			limit_reached = not limit_pin.value() if invert_limit else limit_pin.value()
			if ev != "STOP":
				moved += 1

		if not limit_reached and moved == max_steps:
			# success or we don't care on open limit hit
			enable_pin.value(1)
			save_json("cover.{}".format(state.name), { "state": ev })
			info("moved: Success and state saved!")
			continue
		
		debug("move: limit_reached: {}, moved: {}".format(limit_reached, moved))

		# backoff until limit not detected or backoff_steps reached
		dir_pin.value(not dir_pin.value())
		limit_reached = True
		moved = 0
		debug("move: limit reached, backing off {} steps".format(backoff_steps))
		while limit_reached and moved < backoff_steps:
			onestep(step_pin, delay)
			limit_reached = not limit_pin.value() if invert_limit else limit_pin.value()
			moved += 1

		enable_pin.value(1)
		debug("backoff: limit_reached: {}, moved: {}".format(limit_reached, moved))
		info("moved: State saved: CLOSE")
		save_json("cover.{}".format(state.name), { "state": "CLOSE" })

