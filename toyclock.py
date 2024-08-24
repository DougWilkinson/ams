#toyclock.py

version = (2, 0, 0)

from core import info, latch
from ledclock import LEDClock
#from binary import Binary

#motion = Binary("dining_motion", pin=5, invert=False)
clock = LEDClock("toyclock", pin=5, num_leds=13, 
		hand_index=[6,7,8,9,10,11,0,1,2,3,4,5,12],
		direction_index=[1,-1,1,-1,1,-1,-1,1,-1,1,-1,1],
		edge_index=[6,7,8,9,10,11,0,1,2,3,4,5,12],
		min_hand_length=1, hour_hand_length=1, tail_length=0,
		face_rgb=(1,1,1), hand_rgb=(25,25,25))

async def start(hostname):
		await latch.wait()
