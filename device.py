# device.py
version = (1,0,1)
from msgqueue import MsgQueue
from asyncio import Event

class Device:
	def __init__(self, name, state="", units="", ro=False, dtype="sensor", notifier=None ) -> None:
		self.name = name
		self.dtype = dtype
		self.state = state
		self.units = units
		self.ro = ro
		self.setstate = MsgQueue(1)
		self.event = Event()
		self.publish = Event()
		self.publish.set()
		if notifier:
			# call notifier with this object to setup
			notifier(self)

