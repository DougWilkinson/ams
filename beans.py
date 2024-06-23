# beans.py

# 2,0,1: hass starts on import
version = (2,0,7)
# 2 0 7: set grames init to "0"

import uasyncio as asyncio
from hx711 import HX711
from dispenser import Dispenser
from rgbstatus import RGBStatus
# from button import Button
from alog import info, latch
# notifier is hass
import hass

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces
hx=HX711(hxclock_pin=12, hxdata_pin=14, k=475, max=300, offset=0, samples=5)
rgb = RGBStatus("beans", pin=15, num_leds=3, brightness=15, min_brightness=5)
dispenser = Dispenser("beans", grams="0", tray=hx.high, rgb=rgb.status, hx_average=hx.average, motor_pin=5)
# button = Button("beans", pin=13, pullup=True, invert=True)

async def start(hostname):
	# while True:
	# 	info("beans: grams set: {} - waiting for button".format(dispenser.grams.state))
	# 	await button.wait()
	# 	if dispenser.grams.state == "17":
	# 		rgb.status.set_state("glow_one")
	# 	if dispenser.grams.state == "34":
	# 		rgb.status.set_state("glow_two")
	# 	await asyncio.sleep(4)
	# 	# ready to go, if tray not set, this should just skip
	# 	dispenser.grams.set_state(dispenser.grams.state)
	await latch.wait()
