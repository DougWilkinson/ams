# light.py

from versions import versions
versions[__name__] = 6
# 5: new standard (no hass_setup)
# 6: fixed bri and rgb dtypes

from system import start
from logger import debug
import asyncio
from device import Device

class Light:
	def __init__(self, name="light", state="ON", brightness="10", invert=False) -> None:

		self.state = Device(name, "OFF", dtype="light")
		self.s_bri = Device("{}_bri".format(name), "10", dtype="light", configured=True)
		self.s_rgb = Device("{}_rgb".format(name), "0,255,255", dtype="light", configured=True)
		self.invert = invert

		start(self.state_handler )
		start(self.bri_handler )
		start(self.rgb_handler )


	# define stub methods to be overridden
	def set_state(self, state):
		pass

	def set_brightness(self, brightness):
		pass

	def set_color(self, color):
		pass

	async def state_handler(self):
		async for _ , ev in self.state.q:
			debug("state ev: {}".format(ev))
			if ("ON" in ev and not self.invert) or ("OFF" in ev and self.invert):
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
