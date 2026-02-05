# settings.py

from versions import versions
versions[__name__] = 13

# 2: added microdot and web server/ap mode
# 3: split off profiles, logger and localtime
# 10: refactored
# 11: removed maintain_timezone
# 12: added exception_handler
# 13: fixed info in exception_handler
# 14: added support to start coros with criticality level for status

from os import uname
import asyncio
from machine import soft_reset, freq
from platform import platform
from gc import mem_free
from time import sleep, time
from localtime import offset_time
from sys import print_exception
from io import StringIO

from profiles import Profile, espMAC, get_profiles
from logger import info, error, debug, _exception
# from localtime import offset_time, local_time
from events import status_changed

config = Profile(espMAC)

offset_time(config.timezone)
info("system: timezone set from config: {}".format(config.timezone) )

versions["hostname"] = config.hostname
versions["mac"] = espMAC
versions["freq"] = freq() / 1000000
versions['mpy'] = platform().split('-')[1]
versions['platform'] = uname()[4]
versions['memory'] = mem_free()
versions['reboots'] = config.reboots
versions['server'] = config.mqtt_server
versions['coro_status'] = "online"

# stor coro levels for later use in status value to reflect health of node
# also used to compare levels when updating multiple coro issues, worst level used
coro_criticality_index = {"online":0,
						  "warning":1, 
						  "degraded":2, 
						  "critical":3, 
						  "coro_name": "status_name_if_failed" }

# Notify and start coroutine
def start(coro, level="online"):
	info(f"starting: {coro.__name__} with status impact level: {level}" )
	coro_criticality_index[coro.__name__] = level
	asyncio.create_task(coro() )

def start_warning(coro):
	start(coro, "warning")

def	start_degraded(coro):
	start(coro, "degraded")

def	start_critical(coro):
	start(coro, "critical")

# functools.wraps equivalent
def wraps(wrapped, assigned=('__module__', '__name__', '__doc__')):
	def wrapper(f):
		for attr in assigned:
			try:
				setattr(f, attr, getattr(wrapped, attr))
			except AttributeError:
				pass
		return f
	return wrapper


def exception_handler(func):
	@wraps(func)
	async def wrapped(*args, **kwargs):
		last_error_secs = time()
		exception_limit = 2
		while exception_limit:
			info(f"exception: starting: {func.__name__}")
			try:
				await func( *args, **kwargs )
			except KeyboardInterrupt:
				break
			except Exception as e:
				if time() - last_error_secs < 5:
					exception_limit -= 1
				exception_buffer = StringIO()
				print_exception(e, exception_buffer)
				# error(f"exception({exception_limit}): {func.__name__}: {exception_buffer.getvalue()}" )
				_exception(exception_buffer.getvalue(), func.__name__, exception_limit)
				last_error_secs = time()

		error(f"eh: too many errors - not restarting: {func.__name__}")

	return wrapped

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