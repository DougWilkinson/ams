#bigclock2.py
# testing esp32-s2 on upython v1.23

version = (2, 0, 0)

from alog import info, latch
from ledclock import LEDClock
#from binary import Binary

#motion = Binary("dining_motion", pin=5, invert=False)
clock = LEDClock("bigclock2", pin=12, num_leds=116, 
		hand_index=[10,27,48,65,86,103,8,29,46,67,84,105],
		direction_index=[1,-1,1,-1,1,-1,-1,1,-1,1,-1,1],
		edge_index=[18,19,56,57,94,95,0,37,38,75,76,113,104],
		min_hand_length=7, hour_hand_length=4, tail_length=3,
		face_rgb=(0,0,0), hand_rgb=(25,25,25), always_on=104)

async def start(hostname):
		await latch.wait()
