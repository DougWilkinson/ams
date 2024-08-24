# frontwindow.py

version = (2, 0, 0)

from core import info, latch
from encoderstepper import CoverEncoder

# hardware is initialized (set pins, etc)

cover = CoverEncoder(name="frontwindow", 
		dir_pin=15,
		step_pin=13,
		enable_pin=12,
		enc_pin=14,
		#max_steps=8900, 
		max_steps=18, 
		backoff_steps=5,
		)

async def start(hostname):
		await latch.wait()
