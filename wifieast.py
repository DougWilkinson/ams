# wifieast.py
from versions import versions
versions[__name__] = 1

import uasyncio as asyncio
from core import started, latch, hostname

from wifiscanner import WifiScanner

scanner = WifiScanner(hostname)

async def start(hostname):
	started(hostname)
	while True:
		await latch.wait()
