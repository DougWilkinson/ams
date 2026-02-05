# device.py

from json import loads, dumps

from versions import versions
versions[__name__] = 12
# 4: always put value in q in set_state
# 5: added save_state ,cleaned up u prefixes, load and save for states
# 6: added save_now() to force save
# 10: breaking changes any module needs to be updated
# 11: added debug and error messages
# 12: added backward compatibility for loading "state" vs device name as key

from msgqueue import MsgQueue
from events import device_added
from logger import debug, error
import asyncio

# used by hass to track device publishing and setup
device_list = {}

"""
Device class: Used to hold values that are saved to flash or published to MQTT/HA

name: device name (if "/" in name, it is a topic)
state: initial state (always a string)
units: unit of measurement used mainly by "hass"
dtype: device type used by "hass" for sensor, switch, light, binary_sensor, mqtt

configured (False): set to True to skip notifier setup and just pub/sub
publish (True): Set to False to never publish state
subscribe (True): Set False to never subscribe to topic
needs_publishing (False): Default is to not publish initial state that might be unknown

set_lower (False): set state to lower case when updated with set_state()
save_state (False): If True, save state to flash and load on startup
					filename: dtype.name
mask: function object to use to mask state
      if state is a dictionary, it might mask values like passwords

"""
class Device:
	def __init__(self, 
			name, 
			state="", 
			units="", 
			dtype="sensor", 
			configured=False,
			publish=True, 
			subscribe=True, 
			set_lower=False, 
			needs_publishing=False, 
			save_state=False, 
			mask=lambda x: x ) -> None:
		if name in device_list:
			raise ValueError("device: name already exists: {}".format(name) )
		device_list[name] = self
		self.name = name
		self.dtype = dtype
		self.mask = mask
		self.raw_state = state
		self.state = mask(state)
		self.units = units
		self.q = MsgQueue(1)
		self.event = asyncio.Event()
		self.set_lower = set_lower

		self.configured = configured
		self.subscribe = subscribe
		self.publish = publish
		self.needs_publishing = asyncio.Event()
		if needs_publishing:
			self.needs_publishing.set()

		self.trigger_save = asyncio.Event()

		if save_state:
			asyncio.create_task(self.delayed_save())
			saved = load(self)
			if saved:
				self.raw_state = saved
				self.state = mask(saved)

		# When a device is created, trigger event to notifier
		device_added.set()
		debug("device: created: {} = {}".format(name, self.raw_state) )
	
	def set_state(self, state, topic="state"):
		debug("set: {} = {}".format(self.name, state) )
		self.q.put(topic, str(state) )

		if self.raw_state != str(state):
			self.raw_state = str(state)
			self.state = self.mask(str(state))
			self.needs_publishing.set()
			self.trigger_save.set()

	# delay save to avoid overloading real time response for some devices
	# or when values might change multiple times quickly
	# if multiple triggers happen, save only happens at most every 30 seconds
	async def delayed_save(self):
		while True:
			await self.trigger_save.wait()
			debug("device: delayed_save triggered: {}".format(self.name) )
			await asyncio.sleep(30)

			# check again to see if forced save_now() was done while waiting
			if not self.trigger_save.is_set():
				debug("device: delayed_save cancelled: {}".format(self.name) )
				continue

			save(self)
			self.trigger_save.clear()

	# if forcing a save sooner, cancel the delayed save
	def save_now(self):
		self.trigger_save.clear()
		return save(self)
	
	def on(self):
		self.set_state("ON")

	def off(self):
		self.set_state("OFF")

def load(name, key="run") -> str:

	# if name is a device object, get the name/key from it
	if type(name) == Device:
		filename = name.dtype + "." + name.name
		key = name.name
	else:
		filename = name

	try:
		with open(filename) as file:
			raw = file.readline()
			while raw:
				kv = loads(raw)
				if key and key in kv:
					return kv[key]
				
				# backwards compatibility
				if "state" in kv:
					return kv["state"]
				
				raw = file.readline()
		return ''
	except:
		return ''

def save(name, value="run"):
	
	if type(name) == Device:
		filename = name.dtype + "." + name.name
		key = name.name
		value = name.raw_state
	else:
		filename = name
		key = name

	try:
		with open(filename, "w") as file:
			file.write(dumps({key: value}) )
			file.write("\n")
		debug("device: saved: filename: {}, key: {}, value: {}".format(filename, key, value) )
		return True
	except:
		error("device: failed to save: filename: {}, key: {}, value: {}".format(filename, key, value) )
		return False
