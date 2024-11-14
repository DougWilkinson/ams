# wifiscanner.py

from versions import versions
versions[__name__] = 1

import uasyncio as asyncio
from hass import ha_setup
from device import Device
from time import sleep
from core import wlan, info, error, localtime

class WifiScanner():
	def __init__(self) -> None:
		self.min_db = []
		self.max_db = []
		self.ssid_near = [0]*12
		self.ssid_far = [0]*12
		self.networks = {}

		for i in range(11):
			channel = str(i+1)
			# self.min_db[channel] = Device("min_db_"+channel, "0", units="db", notifier_setup=ha_setup)
			# self.max_db[channel] = Device("max_db_"+channel, "0", units="db", notifier_setup=ha_setup)
			
			# close 0 to -75 db
			# far -76 to -100 db
			self.ssid_near[i+1] = Device("ssid_near_"+channel, "0", units="ssids", notifier_setup=ha_setup)
			self.ssid_far[i+1] = Device("ssid_far_"+channel, "0", units="ssids", notifier_setup=ha_setup)
			
		asyncio.create_task(self.scan())
	
	async def scan(self):
		scan_results = []
		while True:
			scan_results.clear()

			# scan multiple times
			for i in range(10):
				scan_results += wlan.scan()
				info("scanned: {}".format(len(scan_results) ) )
				await asyncio.sleep(10)

			self.networks.clear()
			# dedup scanned results
			for r in scan_results:
				name, bssid, channel, db, security, hidden = r
				
				self.networks[bssid] = { 'name': name, 
					'channel': channel,
					'db': db,
					'security': security,
					'hidden': hidden,
					'first_seen': localtime(),
					'last_seen': localtime()
					}

			self.sort_by_channel()
			error("deduped: {}".format(len(self.networks) ) )
			
			# count near and far based on last scan
			channel_near_count = [0]*12
			channel_far_count = [0]*12
			
			# count channels used
			for bssid,details in self.networks.items():
				channel = details['channel']

				if details['db'] < -75:
					channel_far_count[channel] += 1
				else:
					channel_near_count[channel] += 1

				# if db < self.min_db[channel].state:
				# 	self.min_db[channel].set_state(db)

				# if db > self.max_db[channel].state:
				# 	self.max_db[channel].set_state(db)

			
			info("near: {}".format(channel_near_count))
			info("far: {}".format(channel_far_count))
			
			# update mqtt stats
			for i in range(11):
				channel = i+1
				self.ssid_near[channel].set_state(channel_near_count[channel] )
				self.ssid_far[channel].set_state(channel_far_count[channel] )

			await asyncio.sleep(5)
			sleep(1)

	def sort_by_channel(self):
		# sort the list of networks
		db_sorted_names   = []
		db_sorted_values  = []
		db_sorted_bssids  = []
		db_sorted_channels = []
		
		for bssid, details in self.networks.items():
			name = details['name']
			channel = details['channel']
			if len(db_sorted_names) == 0:
				db_sorted_names.append(name)
				db_sorted_values.append(details['db'])
				db_sorted_bssids.append(bssid)
				db_sorted_channels.append(channel)
				continue
			
			i = 0
			inserted = False
			len_names = len(db_sorted_names)

			while i < len_names:
				if details['channel'] >= db_sorted_channels[i]:
					db_sorted_names.insert(i, name)
					db_sorted_channels.insert(i, channel)
					db_sorted_bssids.insert(i, bssid)
					db_sorted_values.insert(i,details['db'] )
					inserted = True
					break
				i += 1
			if not inserted:
				db_sorted_names.append(name)
				db_sorted_values.append(details['db'])
				db_sorted_bssids.append(bssid)
				db_sorted_channels.append(channel)
		
		for i in range(len(db_sorted_names)):
			name = db_sorted_names[i]
			bssid = db_sorted_bssids[i]
			channel = db_sorted_channels[i]

			_, mo, d, h, mi, _, _, _ = self.networks[bssid]['last_seen']
			last = "{:02d}/{:02d}-{:02d}:{:02d}".format(mo,d,h,mi)
			info("{} : {} : {} db : {}".format(last, channel, db_sorted_values[i], name ) )
