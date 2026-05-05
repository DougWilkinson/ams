# trinity.py

from versions import versions
versions[__name__] = 11
# 10: converted to new standard
# 11: added matrixslidingclock

# from matrixclock import MatrixClock
from matrixslidingclock import MatrixClock

display = MatrixClock(pin=13, num_leds=255, clock_color=(0,2,2), text_color=(0,0,1))
