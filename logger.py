# logger.py

version = (1, 0, 0)

# logging sensor example that will log messages received from specified MQTT topic
# example config line:
# {'hass/sensor/name/temperature/state': { 'module': 'logger' } }
# NOTE: This doesn't use "setup" to add handler as we don't need to configure HA

from alog import info
from aconfig import eventbus, addtask

class Class:
	def __init__(self, name, settings) -> None:
		self.name = name
		info("Creating logger task: {}".format(name))
		addtask(name, self.handler)
		info("logger: task created")

	async def handler(self, event):
		while True:
			await event.wait()
			info(eventbus.get(self.name, "logger: unknown inbus event") )
			event.clear()
	