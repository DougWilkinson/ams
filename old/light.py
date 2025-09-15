# light.py

from versions import versions
versions[__name__] = 1

from core import info, debug, error
import asyncio
from device import Device
from hass import ha_setup, ha_sub

class Light:
	def __init__(self, name="light", state="ON", brightness="10", invert=False) -> None:

		self.state = Device(name, "OFF", dtype="light", notifier_setup=ha_setup)
		self.s_bri = Device("{}_bri".format(name), "10", dtype="light", notifier_setup=ha_sub)
		self.s_rgb = Device("{}_rgb".format(name), "0,255,255", dtype="light", notifier_setup=ha_sub)


		debug("ledlight: create tasks: {}".format(name) )
		asyncio.create_task(self.state_handler(invert) )
		asyncio.create_task(self.bri_handler() )
		asyncio.create_task(self.rgb_handler() )


	def set_state(self, state):
		pass

	def set_brightness(self, brightness):
		pass

	def set_color(self, color):
		pass

	async def state_handler(self, invert):
		async for _ , ev in self.state.q:
			debug("state ev: {}".format(ev))
			if ("ON" in ev and not invert) or ("OFF" in ev and invert):
				debug("state: {} bri: {} rgb: {}".format(self.state.state, self.s_bri.state, self.s_rgb.state))
				self.set_brightness(self.s_bri.state)
				self.set_color(self.s_rgb.state)
				self.set_state("ON")
				continue
			self.set_state("OFF")

	async def bri_handler(self):
		async for _ , ev in self.s_bri.q:
			debug("bri ev: {}".format(ev))
			# trigger rgb to update
			self.set_brightness(ev)

	async def rgb_handler(self):
		async for _ , ev in self.s_rgb.q:
			debug("rgb ev: {}".format(ev))
			# trigger led update
			self.set_color(ev)
