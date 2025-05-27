# bean_dispenser.py
from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
# from hx711 import HX711
from tm1637 import TM1637
from core import latch
from dispenser import Dispenser
from binary import Binary
from switch import Switch
from tray import Tray
import hass

# old hardware 
# display = TMClock(data_pin=0, clock_pin=4, brightness=5)
# tray_sensor = Tray("candy_tray", pin=13, invert=True)
# button = Binary("candy_button", pin=15, invert=False)
# dispense = Switch("candy_dispense", switch_pin=5, off_delay=3, trigger_device=button.state)

display = TM1637("candy",data_pin=21, clock_pin=22, brightness=5)

tray_sensor = Binary("candy_tray", pin=19, invert=True)

button = Binary("candy_button", pin=18, invert=False)

dispense = Switch("candy_dispense", switch_pin=23, off_delay=3, trigger_device=button.state, condition=tray_sensor.state)


async def start(hostname):
	while True:
		await latch.wait()
