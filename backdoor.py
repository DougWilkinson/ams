# backdoor.py

from versions import versions
versions[__name__] = 3

from core import info, latch
from limit import CoverLimit
from binary import Binary

# hardware is initialized (set pins, etc)

motion = Binary("backdoor", pin=4, invert=False)
cover = CoverLimit(name="backdoor", 
		dir_pin=15,
		step_pin=13,
		enable_pin=12,
		max_steps=4000, 
		backoff_steps=350,
		limit_pin=14,
		limit_pullup=1,
		)

async def start(hostname):
		await latch.wait()
