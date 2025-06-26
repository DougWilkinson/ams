# device.py

from json import loads, dumps

from versions import versions
versions[__name__] = 5

# 4: always put value in q in set_state
# 5: added save_state ,cleaned up u prefixes, load and save for states

from msgqueue import MsgQueue
import asyncio

# Device class holds values usually for publishing/subscribing
# state is always a string!
# ro = read only (do not set from notifier)
# dtype = sensor, switch, light, binary_sensor
# notifier = function to call to set up input/output if device changes or is changed
# This is usually MQTT/Homeassistant (ha_setup) from hass.py but could be extended

class Device:
	def __init__(self, name, state="", units="", 
			ro=False, dtype="sensor", notifier_setup=None, 
			set_lower=False, publish=True, save_state=False ) -> None:
		self.name = name
		self.dtype = dtype
		self.state = state
		self.units = units
		self.ro = ro
		self.q = MsgQueue(1)
		self.event = asyncio.Event()
		self.publish = asyncio.Event()
		if publish:
			self.publish.set()
		self.set_lower = set_lower
		if notifier_setup:
			# call notifier with this object to setup
			notifier_setup(self)
		
		self.trigger_save = asyncio.Event()

		if save_state:
			asyncio.create_task(self.delayed_save())
			saved = load(self)
			if saved:
				self.state = saved
	
	def set_state(self, state, topic="state"):
		self.q.put(topic, str(state) )
		if self.state != str(state):
			self.state = str(state)
			self.publish.set()
			self.trigger_save.set()

	# delay save to avoid overloading real time response for some devices
	# or when values might change multiple times quickly
	# if multiple triggers happen, save only happens at most every 30 seconds
	async def delayed_save(self):
		while True:
			await self.trigger_save.wait()
			await asyncio.sleep(30)
			save(self)
			self.trigger_save.clear()

	def on(self):
		self.set_state("ON")

	def off(self):
		self.set_state("OFF")

def load(name, key="run"):

	# if name is a device object, get the name/key from it
	if type(name) == Device:
		filename = name.dtype + "." + name.name
		key = name.name
	else:
		filename = name

	try:
		full = {}
		with open(filename) as file:
			raw = file.readline()
			while raw:
				kv = loads(raw)
				if key and key in kv:
					return kv[key]
				full.update(kv)
				raw = file.readline()
		return full
	except:
		return {}

def save(name, value="run"):
	
	if type(name) == Device:
		filename = name.dtype + "." + name.name
		key = name.name
		value = name.state
	else:
		filename = name
		key = name

	try:
		with open(filename, "w") as file:
			file.write(dumps({key: value}) )
			file.write("\n")
		return True
	except:
		return False
