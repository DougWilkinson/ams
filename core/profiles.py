# profiles.py

from versions import versions
versions[__name__] = 12
# 1: split from settings file
# 10: refactored
# 11: changed load/save for profiles
# 12: added config_valid flag

from device import Device
import json
from os import listdir, remove, rename, stat
from machine import RTC, unique_id
from binascii import hexlify

from gc import mem_free
from time import localtime, time, sleep

from factory_defaults import factory_defaults
import re
from events import config_changed, config_valid
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

# Look in flash for any files starting with sensor.profile
def get_profiles() -> list:
	try:
		return [ f.split(".")[2] for f in listdir() if f.startswith("sensor.profile.") ]
	except:
		return ['Error reading']

def delete_profile(profile_name) -> bool:

	try:
		remove("sensor.profile.{}".format(profile_name) )
		info("delete_profile: deleted: {}".format(profile_name) )
		return True
	except Exception as e:
		info("delete_profile: failed to delete: {}".format(profile_name) )
		error(e)
		return False

# restores to profile name, reboot required after to use new profile
def restore_profile(name) -> bool:
	
	# check for default selected
	if name == espMAC:
		error("restore_profile: cannot restore default profile" ) 
		return True
	
	if name == "last_good":

		try:
			remove("sensor.profile.{}".format(espMAC))
			rename("sensor.profile.last_good", "sensor.profile.{}".format(espMAC) )
			info("restore_profile: restored from: last_good" )
			return True
		except:
			error("restore_profile: failed to restore from: last_good" )
			return False
	
	try:
		remove("sensor.profile.last_good")
	except:
		pass

	try:
		rename("sensor.profile.{}".format(espMAC), "sensor.profile.last_good" )
		rename("sensor.profile.{}".format(name), "sensor.profile.{}".format(espMAC) )
		info("restore_profile: restored from: {}".format(name) )
		return True
	except Exception as e:
		error("restore_profile: failed to restore from: {}".format(name) )
		return False
	
class Profile:

	masked_values = ['mqtt_username', 'mqtt_password', 'wifi_secret', 'password']

	exceptions = ('saved', 'nonpersistent', 'persistent', 'modules')

	# mask secrets
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
			info("profile: merging from: {}".format(self.saved.name))
			self.merge_persistent( json.loads(self.saved.raw_state) )
			result = "Profile loaded from flash:"
		

		# merge from RTC (only if default)
		result = self.load_from_rtc(result)
		
		# if no settings found, try looking for mysecrets
		if self.saved.state == "{}":
			
			try:
				with open(espMAC) as f:
					t = f.readline()
					macfile_hostname = json.loads(t)['run']
					info("profiles: loaded hostname from macfile: {}".format(macfile_hostname) )
			except:
				error("profiles: failed to load hostname from macfile, using espMAC")
				macfile_hostname = espMAC

			try:
				import mysecrets
				self.merge_persistent({"hostname": macfile_hostname, "password": mysecrets.webrepl_pass, "mqtt_server": mysecrets.mqtt_server,
					"mqtt_username": mysecrets.mqtt_user, "mqtt_password": mysecrets.mqtt_pass,
					"wifi_ssid": mysecrets.wifi_name, "wifi_secret": mysecrets.wifi_pass,
					"mqtt_ssl": False })
				info("settings loaded from mysecrets")
			except:
				error("no settings found, saving factory defaults to default profile")

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

		config_valid.set()
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
			info("profile: save: profile: {}".format(self.profile) )
		else:
			error("profile: save: failed: {}".format(self.profile) )

	# save current state with new name
	def save_as(self, name):
		if name == espMAC or name == "":
			error("profile: save_as: invalid profile name: {}".format(name) )
			return

		try:
			with open("sensor.profile.{}".format(name), "w") as f:
				f.write(self.saved.raw_state)
				info("save_profile: saved: {}".format(name) )
				return True
		except Exception as e:
			info("save_profile: failed to save: {}".format(name) )
			return False
	
	def save_to_rtc(self):
		# only save to RTC if default
		if self.profile != espMAC:
			return
		rtc_data = json.dumps({"persistent": self.persistent, "nonpersistent": self.nonpersistent} )
		rtc.memory(rtc_data)

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
	
