#catwater.py

version = (2, 0, 0)

from alog import info, latch
from binary import Binary
from switchmotion import SwitchMotion

motion = Binary("catwater_motion", pin=14, invert=False)
water_relay = SwitchMotion("catwater_fountain", switch_pin=12, trigger=motion, on_seconds=180)

async def start(hostname):
		await latch.wait()

