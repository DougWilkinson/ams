# ntpsync.py

from versions import versions
versions[__name__] = 1

import time
import ntptime

from system import config, start
from logger import info, error

from events import time_synced
import asyncio

info("ntpsync: servers: {}".format(config.ntp_servers) )

async def ntp_sync():

	while True:
		if time.time() - config.timesync_secs < 150:
			continue

		# Looks like time is not synced
		time_synced.clear()

		for host in config.ntp_servers:
			try:
				info("ntpsync: trying host {}".format(host) )
				ntptime.host = host
				ntptime.settime()
				time_synced.set()
				config.timesync_secs = time.time()
				break
			except OSError:
				pass

		if time_synced.is_set():
			continue

		error("ntpsync: all servers failed! trying again in 30 seconds")
		await asyncio.sleep(30)

start(ntp_sync)