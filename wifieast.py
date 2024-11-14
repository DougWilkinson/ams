# wifieast.py
from versions import versions
versions[__name__] = 1

import uasyncio as asyncio
from core import started, latch

from wifiscanner import WifiScanner

scanner = WifiScanner()

async def start(hostname):
	started(hostname)
	while True:
		await latch.wait()
