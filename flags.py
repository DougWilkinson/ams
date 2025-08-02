# flags.py

from versions import versions
versions[__name__] = 1

# 1: changed name to flags and converted to class


from machine import RTC
from gc import mem_free
from time import localtime, time
import binascii
from network import WLAN
import json

# until we are defined
class flags:
	timezone = 19
	log = 7

# build MAC address to use as name if hostname not set
espMAC = str(binascii.hexlify(WLAN().config('mac')).decode() )

# set hostname to MAC for now
hostname = espMAC

class Settings:
	def __init__(self):
		self.settings = {"checksum": 0, 
					  "log": 7, 
					  "timezone": 19, 
					  "boot": 0, 
					  "timesynced": 0, 
					  "reboots": 0,
					  "hostname": espMAC,
					  "wifi_ssid": "",
					  "wifi_secret": "",
					  "ha_topic": "hass",
					  "ha_config": "homeassistant",
					  "mqtt_server": "",
					  "mqtt_username": "",
					  "mqtt_password": "",
					  "mqtt_ssl": True,
					  "ntp_servers": [],
					  "ntp_interval": 60
					  }
		self.load_from_rtc()

	def load_from_rtc(self):
		rtc_data = rtc.memory()
		if rtc_data:
			try:
				self.settings.update(json.loads(rtc_data) )
			except json.JSONDecodeError:
				pass

	def save_to_rtc(self):
		rtc_data = json.dumps(self.settings)
		rtc.memory(rtc_data)

	def set_value(self, name, value):
		self.settings[name] = value
		self.save_to_rtc()

	def get_value(self, name):
		return self.settings.get(name)

	def __getattr__(self, name):
		return self.get_value(name)

	def __setattr__(self, name, value):
			super().__setattr__(name, value)
			self.set_value(name, value)

def offset_time():
	return localtime(time() + ((flags.timezone - 24) * 3600) )

def debug(msg, value=""):
	if 6 <= flags.log:
		# print('\u001b[36m', msg, value, "\u001b[0m" )
		info(msg, lev=6, color='\u001b[36m')

def error(msg):
	info(msg, lev=0, color='\u001b[31m', end="\n")

def info(msg, lev=2, color='\u001b[0m', end="\n"):
	if lev <= flags.log:
		# get time with offset
		dt = offset_time()
		print("{}{:02d}:{:02d}:{:02d}: {}: {}: {}{}".format( color,
			dt[3], dt[4], dt[5], mem_free(), hostname, 
			msg, "\u001b[0m" ), end=end )


config = Settings()