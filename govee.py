# govee5074.py

version = (2,0,0)
# first async version used with ble.py

import struct
from alog import debug, info, error
from device import Device
from hass import ha_setup

class Govee5074:

	# oui match and data pattern for sensor packet
	# These devices send other packets too
	oui = "a4c138"
	data = [10,255,136,236]

	# mac is hexlified version of Mac address (no separators)
	def __init__(self, mac):
		self.mac = mac
		prefix = "govee5074_" + mac + "_"
		
		self.battery = Device(prefix + "battery", "0", 
							units = '%', 
							notifier_setup=ha_setup,
							publish=False)
		self.temp = Device(prefix + "temp", "0", 
					 		units = 'F', 
							notifier_setup=ha_setup,
							publish=False) 
		self.humidity = Device(prefix + "humidity", "0", 
							units = "%", 
							notifier_setup=ha_setup,
							publish=False) 

	def update(self, data):
		if bytes(Govee5074.data) in data:
			self.temp.set_state(str(round((struct.unpack("<h",data[5:7])[0] / 100 * 9 / 5) + 32,1) ) )
			self.humidity.set_state(str(int(round(struct.unpack("<h",data[7:9])[0]/100,0) ) ) )
			self.battery.set_state(data[9])
