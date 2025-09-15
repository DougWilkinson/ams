#lidartest.py

from versions import versions
versions[__name__] = 1

from core import latch, hostname
from vl53l0x import VL53L0X

import asyncio

detector = VL53L0X(hostname)

async def start(hostname):
	await latch.wait()

