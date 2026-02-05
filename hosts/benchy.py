# benchy.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig (no hass_setup)

from logger import info
from cover import Cover
from encoder import Encoder
from steppermotor import StepperMotor
from binary import Binary

mover = StepperMotor(
	dir_pin=6,
	step_pin=5,
	enable_pin=4,
	max_steps=600, 
	backoff_steps=0,
	delay=1250
)

# pin 7 is the magnetic encoder on benchy
#checker = Encoder(7)

#mag_switch = Binary("benchy_limit", pin=7, invert=True)

cover = Cover("benchy", mover=mover)

# test error
info("test error: divide by zero")
a = 1 / 0

# old backdoor config
# ESP32-S3 mini pin configuration
#door = Binary("backdoor", pin=9, invert=False)

#led_lights = LedMotion("backdoor", trigger=door, led_pin=8, num_leds=70, on_seconds=300)

# cover = CoverLimit(name="backdoor", 
# 		dir_pin=3,
# 		step_pin=4,
# 		enable_pin=5,
# 		max_steps=4000, 
# 		backoff_steps=350,
# 		limit_pin=6,
# 		limit_pullup=1,
# 		)
