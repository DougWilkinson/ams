# backdoor.py

from versions import versions
versions[__name__] = 5
# 4: replaced hardware to s3mini

from core import info, latch
from limit import CoverLimit
from binary import Binary
from ledmotion import LedMotion

# hardware is initialized (set pins, etc)

# ESP8266 pin based config
# door = Binary("backdoor", pin=4, invert=False)
# cover = CoverLimit(name="backdoor", 
# 		dir_pin=15,
# 		step_pin=13,
# 		enable_pin=12,
# 		max_steps=4000, 
# 		backoff_steps=350,
# 		limit_pin=14,
# 		limit_pullup=1,
# 		)

# ESP32-S3 mini pin configuration
door = Binary("backdoor", pin=9, invert=False)

led_lights = LedMotion("backdoor", trigger=door, led_pin=8, num_leds=70, on_seconds=300)

cover = CoverLimit(name="backdoor", 
		dir_pin=3,
		step_pin=4,
		enable_pin=5,
		max_steps=4000, 
		backoff_steps=350,
		limit_pin=6,
		limit_pullup=1,
		)

async def start(hostname):
		await latch.wait()
