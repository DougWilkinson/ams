# ntpsynctime.py

version = (2,0,0)

from time import localtime, time
from machine import RTC
import ntptime
from alog import info, error
import uasyncio as asyncio

rtc = RTC()

async def start(ntpservers=None):
	if ntpservers:
		ntpservers.append(ntptime.host)
	else:
		ntpservers = [ntptime.host]

	info("ntpsynctime: servers: {}".format(ntpservers) )
	while True:
		if rtc.memory()[0] == 42:
			for host in ntpservers:
				try:
					info("rtclock: trying ntp host {} ".format(host) )
					ntptime.host = host
					ntptime.settime()
					info("rtclock: success!")
					break
				except OSError:
					error("ntp: Failed!")
					continue
			rtc.memory(b'*')
			await asyncio.sleep(90)

