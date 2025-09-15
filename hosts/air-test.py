# air-test.py

from ble import init_poll_for, init_scan_for, ble_loop
from air import WP6003
from govee import Govee5074
from analog import Analog
from binary import Binary
import asyncio
from core import latch

init_scan_for(Govee5074)
init_poll_for(WP6003)
asyncio.create_task(ble_loop())

co2 = Analog("workbench_co2", pin=34, diff=.1, poll_seconds=60, k=159.3, units="v")
# motion = Binary(name="refrigerator_motion", pin=39)

async def start(hostname):
		await latch.wait()
