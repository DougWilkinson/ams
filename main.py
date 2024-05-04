# main.py
version = (2, 0, 1)
# 2,0,1: added safeboot and flag import

import flag
from alog import info, error, debug, load_config
import json
import uasyncio as asyncio
from machine import reset
from time import sleep

#safeboot
def sb():
	reboot(2)

def reboot(boot=10):
	flag.set('boot',boot)
	print("REBOOTING\r\n>>> ")
	for i in range(boot):
		print(i)
		sleep(1)
				 
	reset()
	while True:
		pass

hostname = load_config()
mod = __import__(hostname)

# load_config() has at minimum a hostname to tell main.py what to import/start

def run():
	asyncio.run(mod.start(hostname))

if flag.get('boot') == 0:
	run()