# blemon1.py
from versions import versions
versions[__name__] = 3

from ble import init_poll_for, init_scan_for, ble_loop
from air import WP6003
from govee import Govee5074
import uasyncio as asyncio

init_scan_for(Govee5074)
init_poll_for(WP6003)

async def start(hostname):
		await ble_loop()
