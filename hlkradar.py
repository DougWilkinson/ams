# hlkradar.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig and no ha_setup

from logger import debug, info, error
from device import Device

class HLKRadar:

	# oui match and data pattern for sensor packet
	# These devices send other packets too
	oui = "acf763"
	data = []

	# mac is hexlified version of Mac address (no separators)
	def __init__(self, mac):
		self.mac = mac
		# prefix = "govee5074_" + mac + "_"
		
		# self.battery = Device(prefix + "battery", "0", 
		# 					units = '%', 
		# 					notifier_setup=ha_setup,
		# 					publish=False)
		# self.temp = Device(prefix + "temp", "0", 
		# 			 		units = 'F', 
		# 					notifier_setup=ha_setup,
		# 					publish=False) 
		# self.humidity = Device(prefix + "humidity", "0", 
		# 					units = "%", 
		# 					notifier_setup=ha_setup,
		# 					publish=False) 

	def update(self, data):
		# if bytes(Govee5074.data) in data:
		# 	self.temp.set_state(str(round((struct.unpack("<h",data[5:7])[0] / 100 * 9 / 5) + 32,1) ) )
		# 	self.humidity.set_state(str(int(round(struct.unpack("<h",data[7:9])[0]/100,0) ) ) )
		# 	self.battery.set_state(data[9])
		info("HLK: {}".format(data) )
