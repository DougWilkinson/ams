# meds.py

from versions import versions
versions[__name__] = 1

import uasyncio as asyncio
from rgbstatus import RGBStatus
from binary import Binary
from core import info, latch
# notifier is hass
import hass

# rgb = RGBStatus("meds_status", pin=5, num_leds=2, brightness=15, min_brightness=5)
# button1 = Binary("meds_button1", pin=14, invert=False )
# button2 = Binary("meds_button2", pin=12, invert=False )
# pills = Binary("meds_container", pin=4, invert=True )

rgb = RGBStatus("meds_status", pin=9, num_leds=2, brightness=15, min_brightness=5)
button1 = Binary("meds_button1", pin=7, invert=False )
button2 = Binary("meds_button2", pin=5, invert=False )
pills = Binary("meds_container", pin=11, invert=True )

async def start(hostname):
	await latch.wait()
