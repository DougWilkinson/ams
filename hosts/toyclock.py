#toyclock.py

from versions import versions
versions[__name__] = 11
# 10: converted to webconfig (no hass_setup)
# 11: add binary support for motion detection and dht22

from ledclock import LEDClock
from binary import Binary
from dht import DHT22
from machine import Pin
from dhtx import DHTX


clock = LEDClock("toyclock", pin=11, num_leds=13, 
		hand_index=[6,7,8,9,10,11,0,1,2,3,4,5,12],
		direction_index=[1,-1,1,-1,1,-1,-1,1,-1,1,-1,1],
		edge_index=[6,7,8,9,10,11,0,1,2,3,4,5,12],
		min_hand_length=1, hour_hand_length=1, tail_length=0,
		face_rgb=(1,1,1), hand_rgb=(25,25,25), invert=True )

motion = Binary("bedroom_motion", pin=12, invert=False)

dht = DHTX("bedroom", DHT22(Pin(8)), poll_sec=60)
