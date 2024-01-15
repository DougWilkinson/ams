# bean_dispenser.py

import asyncio
from tm1637 import TM1637
from dispenser import Dispenser
from button import Button
from tray import Tray
# from hass import Switch, Sensor, BinarySensor

# hardware is initialized (set pins, etc)
display = TM1637("bean_display", data_pin=0, clock_pin=4, brightness=5, speed=180)
dispenser = Dispenser("bean_dispenser", display=display.string.setstate)
button = Button("bean_touch", pin=15, invert=False)
tray_sensor = Tray("bean/tray", pin=13, invert=True)

import hass

async def start():
	asyncio.create_task(hass.start())
	while True:
		await dispenser.dispensed.event.wait()
		await button.wait()
		dispenser.activate.setstate.put("state", "ON")
		await asyncio.sleep(5)

# asyncio.run(dispense())