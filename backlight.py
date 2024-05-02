# backlight.py

import asyncio
import ledlight
from alog import info, latch

# hardware is initialized (set pins, etc)

ledlight.init("backlight")

async def start(hostname):
		await latch.wait()
