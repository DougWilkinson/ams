# bean_dispenser.py

import uasyncio as asyncio
from hx711 import HX711
# from tm1637 import TM1637
from dispenser import Dispenser
from button import Button
from tray import Tray
import hass

# hardware is initialized (set pins, etc)
hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386, offset=0, samples=5)
# display = TM1637("candy_display", data_pin=0, clock_pin=4, brightness=5, speed=180)
tray_sensor = Tray("candy_tray", pin=13, invert=True)
dispenser = Dispenser("candy_dispenser",
					  grams="45", 
					  tray=tray_sensor.is_on, 
					  hx_average=hx.average, 
					  motor_pin=5)
button = Button("candy_button", pin=15, invert=False)


async def start(hostname):
	while True:
		await button.wait()
		dispenser.grams.set_state("40")
		await asyncio.sleep(5)
