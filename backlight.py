# backlight.py

version = (2, 0, 9)
# 208: converted to class version LedMotion
# 209: added superclass cover/limit

from alog import info, latch
#from ledmotion import LedMotion
from encoderstepper import CoverEncoder
from binary import Binary
from switchmotion import SwitchMotion
# hardware is initialized (set pins, etc)

motion = Binary("workspace_motion", pin=5, invert=False)
#led = LedMotion("backlight", trigger=motion, led_pin=14, num_leds=3, on_seconds=15)
cover = CoverEncoder(name="backdisc", max_steps=3, timeout_ms=5000, backoff_steps=1)
switch = SwitchMotion("green_led", switch_pin=0, trigger=motion, on_seconds=20) 

async def start(hostname):
		await latch.wait()
