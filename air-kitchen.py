# air-kitchen.py

from ble import init_poll_for, init_scan_for, ble_loop
from air import WP6003
from govee import Govee5074
from analog import Analog
from binary import Binary
import uasyncio as asyncio

init_scan_for(Govee5074)
init_poll_for(WP6003)

co2 = Analog("kitchen_co2", pin=36, diff=.1, poll_seconds=60, k=159.3, units="v")
motion = Binary(name="refrigerator_motion", pin=39)

async def start(hostname):
		await ble_loop()
