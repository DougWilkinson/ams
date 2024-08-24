#stepper.py

version = (1,0,0)
# async version

from machine import Pin
import time
from core import info, error, debug
from device import Device
import asyncio
from main import load_config
from hass import ha_setup

def init(name, enable_pin=12, step_pin=13, dir_pin=15, 
			enc_pin=4, limit_pin=4, limit_pullup=0, invert_limit=False, 
			timeout=5000, delay=1250, 
			backoff_steps=0, max_steps=1000):
	try:
		state = load_config("cover.saved")
	except:
		state = {'state': 'closed', 'position': 0 }
	
	state = Device(name, state['state'], dtype="cover", notifier_setup=ha_setup)
	enable_pin = Pin(enable_pin, Pin.OUT)
	stop()
	dir_pin = Pin(dir_pin, Pin.OUT)
	step_pin = Pin(step_pin, Pin.OUT)
	
	enc_pin = Pin(enc_pin, Pin.IN)
	timeout = timeout
	last_tick = time.ticks_ms()
	encoder_state = 0
	limit_pin = Pin(limit_pin, limit_pullup) if limit_pin else None
	invert_limit = invert_limit
	backoff_steps = backoff_steps
	# delay is 1250 for 8BY stepper,??? for NEMA?
	delay = delay
	# Actual position (-1 is unknown)
	pos = -1
	
	max_steps = max_steps
	direction = -1
	asyncio.create_task(_activate(activate.set_state) )

def onestep(self):
	step_pin.value(1)
	pass
	step_pin.value(0)
	time.sleep_us(delay)

def at_limit(self):
	return not limit_pin.value() if invert_limit else limit_pin.value()
	
def start(self, direction):
	last_tick = time.ticks_ms()
	encoder_state = enc_pin.value()
	dir_pin.value(direction)
	# limit_state = limit_pin.value()
	if at_limit():
		backoff()
	enable_pin.value(0)

def stop(self):
	enable_pin.value(1)

def still_moving(self):
	if encoder_state != enc_pin.value():
		last_tick = time.ticks_ms()
		encoder_state = enc_pin.value()
	if time.ticks_ms() - last_tick > timeout:
		debug("stepper: move: timeout!")
		return False
	return True

def backoff(self):
	time.sleep_ms(100)
	moved = 0
	info("stepper: home: limit detected, backing off")
	start(1)
	while at_limit() and still_moving():
		onestep()
		moved += 1
	if at_limit():
		error("backoff: timeout during backoff, still at_limit")
		stop()
		status.state = "jammed"
		status.publish = True
		return False

	info("backoff: remaining: {}".format(backoff_steps - moved))
	start(1)
	while backoff_steps > moved:
		onestep()
		moved += 1

	stop()
	return True

def home(self):
	info("stepper: homing")
	start(0)

	# Home
	while still_moving() and not hit_limit():
		onestep()

	stop()

	if not backoff():
		return False
	
	pos = 0
	state.state = "closed"
	state.publish = True
	return True

def set_state_status(self, status="working"):
	if pos == 0:
		status.state = status
		status.publish.set()
		if pos == 0:
			state.state = "closed"
		else:
			state.state = "open"
		state.publish.set()

async def _activate(self, queue):
	async for _, msg in queue:
		info("dispenser: _activate:")
		
		if "open" == msg:
			newsteps = max_steps
		elif "closed" == msg:
			newsteps = 0
		else:
			continue
		
		# set without moving 1st time or skip if already there.
		if pos < 0 or newsteps == pos:
			pos = newsteps
			set_state_status()
			continue
		
		# move in the right direction
		if newsteps > pos:
			step = 1
			start(1)
		else:
			step = -1
			start(0)

		debug("open: moving to: {}".format(newsteps) )
		while (pos != newsteps) and still_moving() and not hit_limit():
			onestep()
			pos += step
		
		stop()
		if newsteps != pos:
			error("stepper: Move failed at position: {}".format(pos) )
			set_state_status(status='jammed')
		else:
			set_state_status()
				