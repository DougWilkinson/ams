# beans.py

# latest version with no display or button
version = (1, 0, 3)

import uasyncio as asyncio
from hx711 import HX711
from dispenser import Dispenser
from rgbstatus import RGBStatus
from button import Button
# notifier is hass
import hass

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces
hx=HX711(hxclock_pin=12, hxdata_pin=14, k=475, offset=0)
rgb = RGBStatus(pin=15, num_leds=3, brightness=15, min_brightness=5)
dispenser = Dispenser("beans_dispenser", grams="34", rgb=rgb.status, hx=hx.raw_read, motor_pin=5)
button = Button("beans_button", pin=13, invert=False)

async def start(hostname):
	asyncio.create_task(hass.start())
	while True:
		rgb.status.set_state(dispenser.grams.state)
		await asyncio.sleep(2)
		rgb.status.set_state("glow_green")
		await button.wait()
		if dispenser.grams.state == "34":
			dispenser.grams.set_state("17")
		else:
			dispenser.grams.set_state("34")

# asyncio.run(dispense())
