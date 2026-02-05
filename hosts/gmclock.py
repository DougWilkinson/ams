# gmclock.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig (no hass_setup)

from tick import Tick
from cover import Cover
from binary import Binary
from steppermotor import StepperMotor

# ESP32-S3 pin configuration (using webconfig and new Cover)
chime_sensor = Binary("gmclock_striking", pin=14, invert=True)

chime_motor = StepperMotor(enable_pin=10, step_pin=11, 
			  dir_pin=9, delay=1250, backoff_steps=2, max_steps=550 )

chime_cover = Cover("gmclock_chime", mover=chime_motor)

clock = Tick("gmclock", tick_pin=12, samples=60)


# ESP8266 pin based config
# chime_sensor = Binary("gmclock_chimes", pin=4, invert=True)
# chime = Cover("gmclock_chime", enable_pin=12, step_pin=15, 
# 			  dir_pin=13, delay=1250, backoff_steps=2, max_steps=550 )
# clock = Tick(hostname, tick_pin=5, pause_pin=14, samples=60)

# # ESP32-S3 pin configuration (before webconfig setup and new Cover)
# chime_sensor = Binary("gmclock_striking", pin=14, invert=True)
# chime = Cover("gmclock_chime", enable_pin=10, step_pin=11, 
# 			  dir_pin=9, delay=1250, backoff_steps=2, max_steps=550 )
# clock = Tick("gmclock", tick_pin=12, pause_pin=8, samples=60)

