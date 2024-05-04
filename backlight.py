# backlight.py

import asyncio
from alog import info, latch
import ledlight
import coverlimit

# hardware is initialized (set pins, etc)

ledlight.init("backlight")
coverlimit.init("backdisc",invert_limit=True)

async def start(hostname):
		await latch.wait()
