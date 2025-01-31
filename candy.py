# bean_dispenser.py
from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
# from hx711 import HX711
from tmclock import TMClock
from core import latch
from dispenser import Dispenser
from binary import Binary
from switch import Switch
from event import Event
from tray import Tray
import hass

# hardware is initialized (set pins, etc)
#hx=HX711(hxclock_pin=12, hxdata_pin=14, k=386, offset=0, samples=5)
display = TMClock(data_pin=0, clock_pin=4, brightness=5)

tray_sensor = Tray("candy_tray", pin=13, invert=True)
# dispenser = Dispenser("candy_dispenser",
# 					  grams="45", 
# 					  tray=tray_sensor.is_on, 
# 					  hx_average=hx.average, 
# 					  motor_pin=5)

button = Binary("candy_button", pin=15, invert=False)
motor = Switch("candy_dispense", switch_pin=5)
dispense = Event(trigger=button.state, target=motor.state, off_delay=0)

async def start(hostname):
	while True:
		await latch.wait()
