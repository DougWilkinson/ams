# hasynctime.py

version = (2,0,0)

from time import localtime, time
from machine import RTC
import json
from device import Device
from alog import info, error, debug, timezone
import uasyncio as asyncio

heartbeat = Device("hass/utc","sensor", notifier_setup=notifier_setup) 

async def start(ntpservers=None):
		self.last_poll = 0
		self.last_set = time()
		# notifier is ha_setup or None
		if notifier_setup:
			self.heartbeat = Device("hass/utc","sensor", notifier_setup=notifier_setup) 
			asyncio.create_task(self.hass_keeptime())
		# list of ntpservers or None
		if ntpservers:
			info("rtclock: ntp servers: {}".format(self.servers) )
			asyncio.create_task(self.ntp_keeptime(ntpservers))

	async def ntp_keeptime(self):
		while True:
			if time() -  self.last_poll < 40:
				await asyncio.sleep(30)
				continue
			self.last_poll = time()
			for host in self.servers:
				try:
					ntptime.host = host
					ntptime.settime()
					self.last_result = localtime()
					info("rtclock: ntp {} time set".format(host) )
					return True
				except OSError:
					error("ntp: error querying: {}".format(host))

	async def hass_keeptime(self):
		global timezone
		if self.heartbeat.mqtt_received:
			self.heartbeat.mqtt_received = False
			j = json.loads(self.heartbeat.value)
			if 'UTC' in j:
				RTC().datetime(tuple(int(i) for i in tuple(j['UTC'].split(','))))
				eventbus['rtc.last'] = time()
				info("rtclock: HA time set")
			if "timezone" in j and timezone != j['timezone']:
					timezone = j['timezone']
					info("rtclock: timezone {} updated".format(timezone) )

