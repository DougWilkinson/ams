# trinity.py

from versions import versions
versions[__name__] = 10
# 10: converted to new standard

from matrixclock import MatrixClock

display = MatrixClock(pin=13, num_leds=255, clock_color=(0,2,2), text_color=(0,0,1))
