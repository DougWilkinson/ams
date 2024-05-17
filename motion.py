# motion.py

# 2,0,0: started separate from ledlight
version = (2, 0, 7)


from machine import Pin
import time
from alog import info, debug
import uasyncio as asyncio
from device import Device
from hass import ha_setup

def init(name="pir", motion_pin=14, led_state=None, on_seconds=5) -> None:

	pin = Pin(motion_pin, Pin.IN)
	motion = Device("{}_motion".format(name), "OFF", dtype="binary_sensor", notifier_setup=ha_setup)

	asyncio.create_task(motion_handler(pin, motion, on_seconds, led_state) )

async def motion_handler(pin, motion, on_seconds, led_state):
	last_motion = time.time()
	in_motion = False
	while True:
		if motion.state == "OFF" and pin.value():
			debug("motion on")
			last_motion = time.time()
			motion.set_state("ON")
			if not in_motion:
				in_motion = True
				if led_state:
					debug("nightlight on")
					led_state.set_state("ON")
		if motion.state == "ON" and not pin.value():
			debug("motion off")
			motion.set_state("OFF")
		if in_motion and time.time() - last_motion > on_seconds:
			in_motion = False
			if led_state:
				debug("nightlight off - time/last: {}/{}".format(time.time(), last_motion))
				led_state.set_state("OFF")
		await asyncio.sleep_ms(300)
