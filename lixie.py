#lixie.py

from versions import versions
versions[__name__] = 3

from core import info, latch, hostname
from lixieclock import LixieClock
from hass import ha_setup
from device import Device

clock = LixieClock(hostname, min_pin=4, hour_pin=13, fade_step=1,
				   flip_delay=40, color=(192,24,0) )

async def start(hostname):
		await latch.wait()
