#timeserverpy

from versions import versions
versions[__name__] = 1

from core import latch, hostname
import asyncio
from gpsntp import GPS

gps = GPS()

async def start(hostname):
	await latch.wait()
