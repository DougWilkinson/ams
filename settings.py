# settings.py

from versions import versions
versions[__name__] = 1

# sensor.wifi.default
# sensor.mqtt.default
# sensor.hass.default
# sensor.device.default

from device import Device
import json
from os import stat, listdir
import asyncio
from machine import RTC, reset
from gc import mem_free
from time import localtime, time, sleep
import binascii
from network import WLAN
from factory_defaults import factory_defaults

rtc=RTC()

# build MAC address to use as name if hostname not set
espMAC = str(binascii.hexlify(WLAN().config('mac')).decode() )

# set hostname to MAC for now
hostname = espMAC
factory_defaults['hostname'] = hostname

masked_values = ['mqtt_username', 'mqtt_password', 'wifi_secret']

def mask_values(unmasked):
	if not unmasked:
		return ''
	unmasked_dict = json.loads(unmasked)
	for k in masked_values:
		if k in unmasked_dict:
			unmasked_dict[k] = '***'
	return json.dumps(unmasked_dict)

exceptions = ('saved', 'nonpersistent', 'persistent')
class Settings:

	def __init__(self, name="default"):
		
		self.nonpersistent	= {"reboots": 0, "timesynced": 0, "boot": 0}
		self.persistent		= {}
		self.save = None

		# merge from factory defaults
		self.merge_persitent(factory_defaults)
		result = "Using factory default settings:"

		# create a device to load/save profile with masking for secrets
		self.saved = Device(espMAC + "." + name, "{}", save_state=True, mask=mask_values)

		# merge from saved flash file
		if self.saved.raw_state != "{}":
			self.merge_persitent( json.loads(self.saved.raw_state) )
			result = "Settings loaded from flash:"

		# merge from RTC (only if default)
		if name == "default":
			result = self.load_from_rtc(result)
		
		print(result)

		# create attrs for both persistent and non-persistent keys and show both
		for k, v in self.nonpersistent.items():
			print("rtc: {}: {}".format(k, v) )
			setattr(self, k, v)

		for k, v in self.persistent.items():
			print("flash: {}: {}".format(k, v) )
			setattr(self, k, v)

		asyncio.create_task(self.update())

	# merge from dict to persistent settings
	def merge_persitent(self, d):
		for k, v in d.items():
			self.persistent[k] = v

	def load_from_rtc(self, result) -> bool:
		rtc_data = rtc.memory()

		if rtc_data:
			try:
				d = json.loads(rtc_data)
				self.persistent = d['persistent']
				self.nonpersistent = d['nonpersistent']
				result = "Settings loaded from RTC:"
			except:
				pass

		return result

	def save_to_flash(self):
		print("Settings saved to flash")
		self.saved.save_now()

	def save_to_rtc(self):
		rtc_data = json.dumps({"persistent": self.persistent, "nonpersistent": self.nonpersistent} )
		rtc.memory(rtc_data)

	def set_value(self, name, value):
		
		if name in self.persistent:
		
			if self.persistent[name] == value:
				return
		
			self.persistent[name] = value
		
			self.saved.set_state(json.dumps(self.persistent) )

		if name in self.nonpersistent:
		
			if self.nonpersistent[name] == value:
				return
		
			self.nonpersistent[name] = value
		
		self.save_to_rtc()

	def get_value(self, name):
		if name in self.persistent:
			return self.persistent[name]
		
		if name in self.nonpersistent:
			return self.nonpersistent[name]

		# Adding this stopped the autocomplete to show everything in dir()
		raise ValueError("unknown: {}".format(name) )

	def __getattr__(self, name):

		if name == "save":
			self.save_to_flash()
			return

		if name in exceptions:
			return super().__getattr__(name)
		return self.get_value(name)

	def __setattr__(self, name, value):
		if name == "save":
			return
		
		if name in exceptions:
			super().__setattr__(name, value)
			return
		if name not in self.persistent and name not in self.nonpersistent:
			raise ValueError("unknown: {}".format(name) )
		else:
			self.set_value(name, value)

	def __dir__(self):
		return list(set(self.persistent.keys() + self.nonpersistent.keys() ) )
	
	# update persistent settings from mqtt
	# Send k/v pairs with = sign to update settings
	# key=value
	#
	# other commands:
	# save <profile_name> - save current settings as new profile before changing default
	# factory reset - reset to defaults
	# profile <profile_name> - change default to profile named profile_name
	# delete <profile_name> - delete profile
	async def update(self):
		async for _ , ev in self.saved.q:
			
			try:
				if "=" in ev:
					k, v = ev.split("=")
					if k in self.persistent:
						self.__setattr__(k, v)
					continue

				k, v = ev.split(" ")

				if k == 'save':
					self.set_default(v)
					continue

				# if k == 'factory':

				# new_profile = Device(self.profile + "." + changes['name'], "", save_state=True, mask=mask_values)

				# new_profile.set_state(ev)
				# new_profile.save_now()

			except:
				error("settings: update: {}".format(ev) )
	def saved_profiles(self) -> list:
		return [ f for f in listdir() if f.startswith("sensor." + self.profile + ".") ]
		
	def set_default(self, name) -> bool:
		try:
			new_profile = Device(self.profile + "." + name, "EMPTY", save_state=True, mask=mask_values)
			if new_profile.state != "EMPTY":
				self.default.set_state(new_profile.raw_state)
				return True
			else:
				print("profile not found: sensor." + self.profile + "." + name)
				return False
		except:
			print("Error: set_default: sensor." + self.profile + "." + name)
			return False

########################################

config = Settings()

def offset_time():
	return localtime(time() + ((config.timezone - 24) * 3600) )

def debug(msg, value=""):
	if 6 <= config.log:
		# print('\u001b[36m', msg, value, "\u001b[0m" )
		info(msg, lev=6, color='\u001b[36m')

def error(msg):
	info(msg, lev=0, color='\u001b[31m', end="\n")

# TODO: add stream buffer to allow webrepl to playback buffer at connect time

def info(msg, lev=2, color='\u001b[0m', end="\n"):
	if lev <= config.log:
		# get time with offset
		dt = offset_time()
		print("{}{:02d}:{:02d}:{:02d}: {}: {}: {}{}".format( color,
			dt[3], dt[4], dt[5], mem_free(), config.hostname, 
			msg, "\u001b[0m" ), end=end )

def start(msg):
	info("starting: {}".format(msg) )

#safeboot
def sb():
	reboot(2)

def reboot(boot=10):
	config.reboots = 0
	config.boot = boot
	print("REBOOTING\r\n>>> ")
	for i in range(boot):
		print(i)
		sleep(1)
				 
	reset()
	while True:
		pass


# profile_attributes = { 'wifi': { 'ssid': '', 'secret': '' },
# 					'mqtt': {'server': '', 'port': 1883, 'ssl': False, 'username': '', 'password': ''},
# 					'hass': {'config_topic_prefix': 'homeassistant', 'topic_prefix': 'hass'},
# 					'device': {'webrepl_password': '', 'hostname': ''},
# 					'ntp': {'servers': [], 'interval': 60}
# 				}

# masked_values = ['mqtt_password', 'wifi_secret']

# def mask_values(unmasked):
# 	if not unmasked:
# 		return ''
# 	unmasked_dict = json.loads(unmasked)
# 	for k in masked_values:
# 		if k in unmasked_dict:
# 			unmasked_dict[k] = '***'
# 	return json.dumps(unmasked_dict)

# # Add instances here to be updated by hass if it is loaded
# hass_updated = []

# class Profile:
# 	def __init__(self, name="default", **kwargs):
# 		self.name = name

# 		# create a device to load/save profile with masking for secrets
# 		self.default = Device("settings." + name, "", save_state=True, mask=mask_values)
# 		# save reference here for hass to reference if loaded
# 		hass_updated.append(self.default)
		
# 		# combine defaults and saved values
# 		self.attributes = config.settings
# 		saved = json.loads(self.default.raw_state)

# 		self.attributes.update(saved)

# 		self.attributes['profile'] = name

# 		# finally override settings with kwargs if provided		
# 		if kwargs:
# 			for k, v in kwargs.items():
# 				if k in self.attributes:
# 					self.attributes[k] = v
# 				else:
# 					raise ValueError("unknown attribute: {}: {}".format(k, v) )
# 			print("Saving updated kwargs for profile: {}".format(self.default.name) )
# 			self.default.set_state( json.dumps( self.attributes) )

# 		for k, v in self.attributes.items():
# 			setattr(self, k, v)

# 		asyncio.create_task(self.update())

# 	async def update(self):
# 		async for _ , ev in self.default.q:
# 			changes = json.loads(ev)

# 			if 'set_default' in changes:
# 				new_profile_name = changes['set_default']
# 				self.set_default(new_profile_name)
# 				continue

# 			new_profile = Device(self.profile + "." + changes['name'], "", save_state=True, mask=mask_values)

# 			new_profile.set_state(ev)
# 			new_profile.save_now()

# 	def saved_profiles(self) -> list:
# 		return [ f for f in listdir() if f.startswith("sensor." + self.profile + ".") ]
		
# 	def set_default(self, name) -> bool:
# 		try:
# 			new_profile = Device(self.profile + "." + name, "EMPTY", save_state=True, mask=mask_values)
# 			if new_profile.state != "EMPTY":
# 				self.default.set_state(new_profile.raw_state)
# 				return True
# 			else:
# 				print("profile not found: sensor." + self.profile + "." + name)
# 				return False
# 		except:
# 			print("Error: set_default: sensor." + self.profile + "." + name)
# 			return False

