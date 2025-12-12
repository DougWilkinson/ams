# settings.py

from versions import versions
versions[__name__] = 11

# 2: added microdot and web server/ap mode
# 3: split off profiles, logger and localtime
# 10: refactored
# 11: removed maintain_timezone

from os import uname
import asyncio
from machine import soft_reset, freq
from platform import platform
from gc import mem_free, mem_alloc
from time import sleep
from localtime import offset_time

from profiles import Profile, espMAC, get_profiles
from logger import info, error, debug
# from localtime import offset_time, local_time

config = Profile(espMAC)

offset_time(config.timezone)
info("system: timezone set from config: {}".format(config.timezone) )

versions["hostname"] = config.hostname
versions["mac"] = espMAC
versions["freq"] = freq() / 1000000
versions['mpy'] = platform().split('-')[1]
versions['platform'] = uname()[4]
versions['memory'] = mem_free() + mem_alloc()
versions['reboots'] = config.reboots
versions['server'] = config.mqtt_server

# Notify and start coroutine
def start(coro):
	info("starting: {}".format(coro.__name__) )
	asyncio.create_task(coro() )

#safeboot
def sb():
	reboot(2)

def reboot(boot=10):
	config.reboots = 0
	config.boot_mode = boot
	print("REBOOTING\r\n>>> ")
	for i in range(boot):
		print(i)
		sleep(1)
				 
	soft_reset()
	while True:
		pass

# async def maintain_timezone():
	
# 	last_timezone = -99

# 	while True:
# 		if config.timezone != last_timezone:
# 			offset_time(config.timezone)
# 			last_timezone = config.timezone
# 		await asyncio.sleep(5)

# start(maintain_timezone)