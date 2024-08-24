# main.py
version = (2, 0, 9)
# 209: genhash use uhashlib/ubinascii

import flag
from core import info, error, started, stopped
from core import hostname, genhash, reboot
import uasyncio as asyncio
import webrepl
from time import sleep

def run():
	mod = __import__(hostname)
	asyncio.run(mod.start(hostname))

# 2 = safeboot, do not start named module
# 1 = delay start to allow remote console time

if flag.get('boot') != 2:
	if flag.get('boot') == 1:
		delay = 30
		while delay > 0 and webrepl.client_s is None:
			sleep(1)
			delay -= 1
	run()