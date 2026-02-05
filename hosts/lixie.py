#lixie.py

from versions import versions
versions[__name__] = 10
# 10: support for webconfig (no hass_setup)

from lixieclock import LixieClock

#clock = LixieClock(hostname, min_pin=4, hour_pin=13, fade_step=1,
#				   flip_delay=40, color=(192,24,0) )

clock = LixieClock("lixie", min_pin=13, hour_pin=11, fade_step=1,
				   flip_delay=40, color=(192,24,0) )

