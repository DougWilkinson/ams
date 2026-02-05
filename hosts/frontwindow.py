# frontwindow.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig and no hass_setup

from cover import Cover
from encoder import Encoder
from steppermotor import StepperMotor

mover = StepperMotor(
	dir_pin=8,
	step_pin=9,
	enable_pin=10,
	max_steps=18, 
	backoff_steps=5,
	delay=1250
)

checker = Encoder(11)

cover = Cover("frontwindow", mover=mover, checker=checker)


# hardware is initialized (set pins, etc)

# ESP8266 pin based config
# cover = CoverEncoder(name="frontwindow", 
# 		dir_pin=15,
# 		step_pin=13,
# 		enable_pin=12,
# 		enc_pin=14,
# 		#max_steps=8900, 
# 		max_steps=18, 
# 		backoff_steps=5,
# 		)

# REPLACED WITH ABOVE WITH NEW VERSIONS
# ESP32-S3 mini pin configuration
# cover = CoverEncoder(name="frontwindow", 
# 		dir_pin=8,
# 		step_pin=9,
# 		enable_pin=10,
# 		enc_pin=11,
# 		#max_steps=8900, 
# 		max_steps=18, 
# 		backoff_steps=5,
# 		)

# async def start(hostname):
# 		await latch.wait()
