# ledlight.py

# 2,0,0: changed to non-class based
# 2,0,1: multi-instance support?
version = (2, 0, 1)


from machine import Pin
import time
from alog import info, debug
import asyncio
from neopixel import NeoPixel
from device import Device
from hass import ha_setup

def clear_leds(leds):
	leds.fill((0,0,0))
	leds.write()

def set_leds(leds, s_rgb, s_bri):
	bri = int(s_bri.state) / 255
	r, g, b = s_rgb.state.split(",")
	#bri = int(s_bri.state)/255
	rgb = (int( int(r) * bri), int( int(g) * bri), int(int(b) * bri) )
	leds.fill(rgb)
	leds.write()

# def ha_setup(device):
# 	pass

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
def init(name="led", led_pin=14, num_leds=3, motion_pin=5, on_seconds=5) -> None:

	state = Device(name, "OFF", dtype="light", notifier_setup=ha_setup)
	s_bri = Device("{}_bri".format(name), "10", dtype="light", notifier_setup=ha_setup)
	s_rgb = Device("{}_rgb".format(name), "0,255,255", dtype="light", notifier_setup=ha_setup)

	leds = NeoPixel(Pin(led_pin), num_leds)
	clear_leds(leds)

	motion_pin = Pin(motion_pin, Pin.IN)
	motion = Device("{}_motion".format(name), "OFF", dtype="binary_sensor", notifier_setup=ha_setup)

	debug("ledlight: create tasks: {}".format(name) )
	asyncio.create_task(state_handler(state, leds, s_rgb, s_bri) )
	asyncio.create_task(bri_handler(s_bri, state) )
	asyncio.create_task(rgb_handler(s_rgb, state) )
	asyncio.create_task(motion_handler(motion_pin, motion, on_seconds, state) )

async def state_handler(state, leds, s_rgb, s_bri):
	async for _ , ev in state.q:
		debug("state ev: {}".format(ev))
		if "ON" in ev:
			debug("setting leds to {}/{}".format(s_bri.state, s_rgb.state))
			set_leds(leds, s_rgb, s_bri)
			continue
		clear_leds(leds)

async def bri_handler(s_bri, state):
	global bri
	async for _ , ev in s_bri.q:
		debug("bri ev: {}".format(ev))
		# trigger rgb to update
		state.set_state(state.state)

async def rgb_handler(s_rgb, state):
	async for _ , ev in s_rgb.q:
		debug("rgb ev: {}".format(ev))
		# trigger led update
		state.set_state(state.state)

async def motion_handler(motion_pin, motion, on_seconds, state):
	last_motion = time.time()
	in_motion = False
	while True:
		if motion.state == "OFF" and motion_pin.value():
			debug("motion on")
			last_motion = time.time()
			motion.set_state("ON")
			if not in_motion:
				debug("nightlight on")
				in_motion = True
				state.set_state("ON")
		if motion.state == "ON" and not motion_pin.value():
			debug("motion off")
			motion.set_state("OFF")
		if in_motion and time.time() - last_motion > on_seconds:
			debug("nightlight off - time/last: {}/{}".format(time.time(), last_motion))
			in_motion = False
			state.set_state("OFF")
		await asyncio.sleep_ms(300)
