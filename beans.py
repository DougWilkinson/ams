# beans.py

# remove tray_sensor
version = (1,0,1)

import asyncio
from hx711 import HX711
from tm1637 import TM1637
from dispenser import Dispenser
from button import Button
from tray import Tray
# from hass import Switch, Sensor, BinarySensor

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386)
# k=475 for small kitchen scale/coffee beans for grams
# k=13463 for ounces
hx=HX711(hxclock_pin=12, hxdata_pin=14, k=475, offset=0)
display = TM1637("beans_display", data_pin=0, clock_pin=4, brightness=5, speed=180)
# tray_sensor = Tray("beans/tray", pin=13, invert=True)
dispenser = Dispenser("beans_dispenser", cycles=3, hx_read=hx.raw_read, motor_pin=5, display=display.string.setstate)
button = Button("beans_touch", pin=15, invert=False)

import hass

async def start():
	asyncio.create_task(hass.start())
	while True:
		await dispenser.dispensed.event.wait()
		await button.wait()
		dispenser.activate.setstate.put("state", "ON")
		await asyncio.sleep(5)

# asyncio.run(dispense())
