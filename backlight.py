# backlight.py

from versions import versions
versions[__name__] = 3

from core import info, latch
#from ledmotion import LedMotion
from encoderstepper import CoverEncoder
from binary import Binary
from switch import Switch
from event import Event
# hardware is initialized (set pins, etc)

cover = CoverEncoder(name="backdisc", max_steps=3, timeout_ms=5000, backoff_steps=1)

#led = LedMotion("backlight", trigger=motion, led_pin=14, num_leds=3, on_seconds=15)
# using led on gpio 0 instead of neopixel for testing
motion = Binary("workspace_motion", pin=5, invert=False)
switch = Switch("green_led", switch_pin=0)
event = Event(motion.state, switch.state, off_delay=10) 

async def start(hostname):
		await latch.wait()
