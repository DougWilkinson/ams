# dhtx.py

from versions import versions
versions[__name__] = 3
# 2,0,0: non-class version

from core import started, error
from device import Device
import uasyncio as asyncio
from hass import ha_setup

def init(name, dht, poll_sec=60):
	temp = Device(name + "_temp", "0", "F", notifier_setup=ha_setup, publish=False)
	humidity = Device(name + "_humidity", "0", "%", notifier_setup=ha_setup, publish=False)
	asyncio.create_task(handler(dht, temp, humidity, poll_sec))
	
async def handler(dht, temp, humidity, poll_sec):
	started(temp.name)
	while True:
		# readtemp
		for i in range(4):
			try:
				dht.measure()
				temp.set_state( round( (dht.temperature() * 9 / 5) + 32,1) )
				humidity.set_state(int(round(dht.humidity(),0) ) )
				break
			except OSError:
				error("dht: {} read timeout".format(temp.name) )
				await asyncio.sleep(2)
	
		await asyncio.sleep(poll_sec)