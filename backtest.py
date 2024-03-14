# backtest.py

import asyncio
from binary_sensor import BinarySensor
# from hass import Switch, Sensor, BinarySensor

# hardware is initialized (set pins, etc)
motion = BinarySensor("backtest_motion", pin=5, invert=False)

import hass

async def start(hostname):
	asyncio.create_task(hass.start())
	while True:
		await motion.wait()
		await asyncio.sleep(5)

# asyncio.run(dispense())