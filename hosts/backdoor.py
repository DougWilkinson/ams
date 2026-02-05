# backdoor.py

from versions import versions
versions[__name__] = 10
# 4: replaced hardware to s3mini
# 10: converted several modules and using webconfig (no ha_setup)

from logger import info

from steppermotor import StepperMotor

door_stepper = StepperMotor(dir_pin=3, step_pin=4, enable_pin=5, max_steps=4000, backoff_steps=350 )

from binary import Binary
from cover import Cover

# Pin.PULL_UP = 2
# Pin.PULL_DOWN = 1
close_limit_switch = Binary("curtain_limit", pin=6, pullup=2)
curtains = Cover("backdoor_curtain", mover=door_stepper, close_limit=close_limit_switch)

from machine import Pin
from neopixel import NeoPixel

# define the neopixels pin and count and clear
leds = NeoPixel(Pin(8), 70)
leds.fill((0,0,0))
leds.write()

from ledmotion import LedMotion

# ESP32-S3 mini pin configuration
door = Binary("backdoor", pin=9, invert=False)
led = LedMotion("backdoor_overhead", leds, trigger=door, off_delay=300)

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


# # old backdoor config
# led_lights = LedMotion("backdoor", trigger=door, led_pin=8, num_leds=70, on_seconds=300)
