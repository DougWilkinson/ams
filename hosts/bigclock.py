#bigclock.py

from versions import versions
versions[__name__] = 11
# 10: converted to webconfig (no hass_setup)
# 11: added workbench lid

from ledclock import LEDClock
from binary import Binary
from analog import Analog
# motion = Binary("dining_motion", pin=5, invert=False)

# s3 mini pin configuration
clock = LEDClock("bigclock", pin=13, num_leds=116, 
		hand_index=[10,27,48,65,86,103,8,29,46,67,84,105],
		direction_index=[1,-1,1,-1,1,-1,-1,1,-1,1,-1,1],
		edge_index=[18,19,56,57,94,95,0,37,38,75,76,113,104],
		min_hand_length=7, hour_hand_length=4, tail_length=3,
		face_rgb=(0,0,0), hand_rgb=(25,25,25), always_on=104)

motion = Binary("dining_motion", pin=10, invert=False)

workbench_lid = Binary("workbench_lid", pin=7, invert=False, pullup=2)

air_co2 = Analog("workbench_co2", pin=8, diff=.1, poll_seconds=60, k=159.3, units="v")
