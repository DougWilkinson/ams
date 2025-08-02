# main.py

from versions import versions
versions[__name__[2:-2]] = 3

from settings import config, hostname, info, error, debug

import asyncio
from time import sleep

if config.wifi:
	import wifi

"""
if wifi config is True, 
Look for modules in config and load any that are set to True
(wifi factory default is on)
create tasks (they start later)

wait up to 10 seconds for wifi (hostname should be known)
wait up to 20 seconds if boot = 5 (reload after update)

"""

# import modules - each module should only do bare minimum when being imported
# shut off gpios, clear leds or display, etc. NO WAITING

for k, v in config.items():
	if "module_" in k and v:
		try:
			mod = __import__(k.split("_")[1])
		except:
			continue

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