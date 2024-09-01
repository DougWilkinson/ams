# device.py

from versions import versions
versions[__name__] = 3

# 209: always put value in q in set_state

from msgqueue import MsgQueue
from uasyncio import Event

# Device class holds values usually for publishing/subscribing
# state is always a string!
# ro = read only (do not set from notifier)
# dtype = sensor, switch, light, binary_sensor
# notifier = function to call to set up input/output if device changes or is changed
# This is usually MQTT/Homeassistant (ha_setup) from hass.py but could be extended

class Device:
	def __init__(self, name, state="", units="", 
			ro=False, dtype="sensor", notifier_setup=None, 
			set_lower=False, publish=True ) -> None:
		self.name = name
		self.dtype = dtype
		self.state = state
		self.units = units
		self.ro = ro
		self.q = MsgQueue(1)
		self.event = Event()
		self.publish = Event()
		if publish:
			self.publish.set()
		self.set_lower = set_lower
		if notifier_setup:
			# call notifier with this object to setup
			notifier_setup(self)
	
	def set_state(self, state, topic="state"):
		self.q.put(topic, str(state) )
		if self.state != str(state):
			self.state = str(state)
			self.publish.set()
