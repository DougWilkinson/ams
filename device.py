# device.py

from msgqueue import MsgQueue
from asyncio import Event

class Device:
	def __init__(self, name, state="", notifier=None ) -> None:
		self.name = name
		self.state = state
		self.units = ""
		self.setstate = MsgQueue(1)
		self.event = Event()
		self.publish = Event()
		self.publish.set()
		if notifier:
			# instantiate notifier with this object
			self.notifier = notifier(self)

