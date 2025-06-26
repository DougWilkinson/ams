# main.py

from versions import versions
versions[__name__[2:-2]] = 3

import flag
from core import info, error, started, reboot
from core import espMAC, hostname, latch
import asyncio
import webrepl
from time import sleep

async def start(hostname):
	started("bootstrap")
	while True:
		await latch.wait()
def run():
	mod = __import__(hostname)
	asyncio.run(mod.start(hostname))

if espMAC == hostname:
	import hass
	asyncio.run(start(hostname))
	reboot()

# 2 = safeboot, do not start named module
# 1 = delay start to allow remote console time

if flag.get('boot') != 2:
	delay = 20
	while delay > 0 and webrepl.client_s is None:
		sleep(1)
		delay -= 1
	run()

flag.clear('boot')