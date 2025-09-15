# profiles.py

from versions import versions
versions[__name__] = 1
# 1: split from settings file

from device import Device
import json
from os import listdir, remove
from machine import RTC, unique_id
from binascii import hexlify

from gc import mem_free
from time import localtime, time, sleep

from factory_defaults import factory_defaults
import re
from events import config_changed
from logger import info, error

espMAC = hexlify(unique_id()).decode()

profile_field_display = { "system": ("hostname", "password", "log", "timezone"), 
				"wifi": ("wifi","wifi_ssid", "wifi_secret"), 
				"mqtt": ("mqtt_ssl", "mqtt_server", "mqtt_username", "mqtt_password"), 
				"ntp": ("ntp_servers", "ntp_interval"),
				"hass": ("ha_topic", "ha_config")
				}

rtc=RTC()

# set hostname to MAC if not overridden from flash or RTCmem
factory_defaults['hostname'] = espMAC

def get_profiles() -> list:
	try:
		return [ f.split(".")[2] for f in listdir() if f.startswith("sensor.profile.") ]
	except:
		return ['Error reading']

def delete_profile_by_name(profile_name) -> bool:

	try:
		remove("sensor.profile.{}".format(profile_name) )
		info("delete_profile: deleted: {}".format(profile_name) )
		return True
	except Exception as e:
		info("delete_profile: failed to delete: {}".format(profile_name) )
		error(e)
		return False

class Profile:

	masked_values = ['mqtt_username', 'mqtt_password', 'wifi_secret', 'password']

	exceptions = ('saved', 'nonpersistent', 'persistent', 'modules')

	def mask(unmasked) -> str:
		
		#print(unmasked)
		
		if not unmasked or type(unmasked) != str:
			return ''
		masked_dict = json.loads(unmasked)
		
		for k in Profile.masked_values:
			if k in masked_dict:
				masked_dict[k] = '***'
		return json.dumps(masked_dict)

	def __init__(self, name):
		
		self.nonpersistent	= {"reboots": 0, "timesync_secs": -99999, "boot_mode": 0, "last_wifi_ssid": ""}
		self.persistent		= {"profile": name}
		self.modules = []

		# merge from factory defaults
		self.merge_persistent(factory_defaults)
		result = "Using factory default settings:"

		# create a device to load/save profile with masking for secrets
		self.saved = Device("profile." + name, "{}", save_state=True, mask=Profile.mask)

		# merge from saved flash file
		if self.saved.raw_state and self.saved.raw_state != "{}":
			print("merging from flash", self.saved.raw_state)
			self.merge_persistent( json.loads(self.saved.raw_state) )
			result = "Profile loaded from flash:"

		# merge from RTC (only if default)
		if name == espMAC:
			result = self.load_from_rtc(result)
			if self.saved.state == "{}":
				print("no settings found in flash or RTC, saving factory defaults to default profile")
				self.saved_from_profile = espMAC
				self.save()
		
		#print(result)

		# create attrs for both persistent and non-persistent keys and show both
		for k, v in self.nonpersistent.items():
			print("rtc: {}: {}".format(k, v) )
			setattr(self, k, v)

		for k, v in self.persistent.items():
			print("flash: {}: {}".format(k, v) )
			setattr(self, k, v)
			if "modules_" in k:
				self.modules.append((k.split("_")[1]) )

		#asyncio.create_task(self.update())

	# merge from dict to persistent settings
	def merge_persistent(self, d):
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

	def add_persistent(self, name, value):
		self.persistent[name] = None
		self.set_value(name, value)
	
	def	add_nonpersistent(self, name, value):
		self.nonpersistent[name] = value
		self.set_value(name, value)

	def save(self):
		self.saved.set_state(json.dumps(self.persistent))
		
		# save to RTC only if default profile
		if self.profile == espMAC:
			self.save_to_rtc()

		if self.saved.save_now():
			print("save: profile saved as {}".format(self.profile) )
		else:
			print("save: failed to save profile: {}".format(self.profile) )

	def save_as(self, name):
		if name == espMAC or name == "":
			print("save_as: invalid profile name!")
			return
		new_profile = Device("profile." + name, "" )
		new_profile.profile = name
		new_profile.save_now()
		self.profile = name
		self.save()

	def save_to_rtc(self):
		# only save to RTC if default
		if self.profile != espMAC:
			return
		rtc_data = json.dumps({"persistent": self.persistent, "nonpersistent": self.nonpersistent} )
		rtc.memory(rtc_data)

	def return_to_factory_defaults(self):

		self.nonpersistent = factory_defaults
		self.save_to_rtc()

		self.persistent = factory_defaults
		self.save()
		
		print("settings returned to factory defaults")

	def set_value(self, name, value):
		
		if name in self.persistent:
		
			if self.persistent[name] == value:
				return
		
			self.persistent[name] = value

			# signal config change to other modules
			config_changed.set()
			
			self.saved.set_state(json.dumps(self.persistent) )

		if name in self.nonpersistent:
		
			if self.nonpersistent[name] == value:
				return
		
			self.nonpersistent[name] = value
		
		self.save_to_rtc()
		
		if not hasattr(self, name):
			setattr(self, name, value)

	def get_value(self, name):
		if name in self.persistent:
			return self.persistent[name]
		
		if name in self.nonpersistent:
			return self.nonpersistent[name]

		# Adding this stopped the autocomplete to show everything in dir()
		raise ValueError("unknown: {}".format(name) )

	def __getattr__(self, name):

		if name in Profile.exceptions:
			return super().__getattr__(name)
		return self.get_value(name)

	def __setattr__(self, name, value):

		if name in Profile.exceptions:
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

	# async def update(self):
	# 	async for _ , ev in self.saved.q:
			
	# 		try:
	# 			if "=" in ev:
	# 				k, v = ev.split("=")
	# 				if k in self.persistent:
	# 					self.__setattr__(k, v)
	# 				continue

	# 			k, v = ev.split(" ")

	# 			if k == 'save':
	# 				self.set_default(v)
	# 				continue

	# 			# if k == 'factory':

	# 			# new_profile = Device(self.profile + "." + changes['name'], "", save_state=True, mask=mask_values)

	# 			# new_profile.set_state(ev)
	# 			# new_profile.save_now()

	# 		except:
	# 			error("settings: update: {}".format(ev) )
		
	def set_as_default(self, name) -> bool:
		if self.profile != espMAC:
			info("set_default: this is not the default profile!")
			return True
		
		try:
			# load profile to use
			new_profile = Device("profile." + name, "{}", save_state=True, mask=Profile.mask)
			
			# if profile exists, use it
			if new_profile.state != "{}":
				
				new_persistent = json.loads(new_profile.raw_state)
				new_persistent['profile'] = espMAC
				new_persistent['saved_from_profile'] = name
				self.merge_persistent(new_persistent)
				self.save()

				# signal config change to other modules
				config_changed.set()
			else:
				info("set_default: profile not found: sensor.pofile." + name)
				return False
		except Exception as e:
			info("set_default: Error setting default to: sensor.profile." + name)
			info("Exception: ",e)
			return False

