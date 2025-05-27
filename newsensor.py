# newsensor.py

from versions import versions
versions[__name__] = 3

import uasyncio as asyncio
from core import info, offset_time, latch, hostname


async def start(hostname):
		await latch.wait()

asyncio.run(start(hostname))
