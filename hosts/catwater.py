#catwater.py

from machine import Pin
water_pin = Pin(37, Pin.OUT)
water_pin.off()

from versions import versions
versions[__name__] = 10

from binary import Binary
from switch import Switch

#spare at 33
#motion = Binary("catwater_motion", pin=14, invert=False)
#water_relay = SwitchMotion("catwater_fountain", switch_pin=12, trigger=motion, on_seconds=180)

motion = Binary("catwater_motion", pin=39, invert=False)

water_relay = Switch("catwater_fountain", water_pin, off_delay=180, trigger_device=motion.state)
