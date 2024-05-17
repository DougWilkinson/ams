# stove.py

version = (2, 0, 7)

import uasyncio as asyncio
from dht import DHT22
from machine import Pin
import dhtx
from alog import started, latch
# notifier is hass
from hass import ha_setup
from device import Device
import motion

dhtx.init("stove", DHT22(Pin(13) ) )
dhtx.init("sink", DHT22(Pin(4) ) )
motion.init("stove", 14 )

async def start(hostname):
	started(hostname)
	while True:
		await latch.wait()
