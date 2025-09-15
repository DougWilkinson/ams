# rgblight.py

from versions import versions
versions[__name__] = 3
# 200: taken from ledlight to break out light.rgb only

from device import Device
from hass import ha_setup, ha_sub

# {'light/name': {'module':'ledlight', 'leds': 20, 'pin':14, 'rgb': '192,24,0' }}
class RGBlight:
	def __init__(self, name) -> None:
		self.state = Device(name, "OFF", dtype="light", notifier_setup=ha_setup)
		self.s_bri = Device("{}_bri".format(name), "10", dtype="light", notifier_setup=ha_sub)
		self.s_rgb = Device("{}_rgb".format(name), "0,255,255", dtype="light", notifier_setup=ha_sub)
