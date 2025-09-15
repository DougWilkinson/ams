# stove.py

from versions import versions
versions[__name__] = 3

import asyncio
from dht import DHT22
from machine import Pin
import dhtx
from core import started, latch
# notifier is hass
from hass import ha_setup
from device import Device
import motion
from analog import Analog

# dhtx.init("stove", DHT22(Pin(13) ) )
dhtx.init("sink", DHT22(Pin(11) ) )
motion.init("stove", 13 )
co2 = Analog("stove_co2", pin=9, diff=.1, poll_seconds=60, k=159.3, units="v")


async def start(hostname):
	started(hostname)
	while True:
		await latch.wait()
