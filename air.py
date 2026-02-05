#air.py

from versions import versions
versions[__name__] = 5
# 5: using refactored code (no hass_setup)

from system import error
from device import Device

class WP6003:

	oui = '600303'
	uuid = 0xFFF1
	write_value = 171

	def __init__(self, mac):
		self.mac = mac

		name = "wp6003_" + mac + "_"
		self.temp = Device(name + "temperature", 
							"0",
							units = 'F' )
		self.tvoc = Device(name + "TVOC", 
							"0", 
							units = "mg/m3" )
		self.hcho = Device(name + "HCHO", 
							"0", 
							units = "mg/m3" )
		self.co2 = Device(name + "CO2", 
							"0", 
							units = "ppm" )

	def update(self, data):
		try:
			self.temp.set_state(round( ( data[6]*256 + data[7]) * 0.18 + 32 , 1 ) ) 
			self.tvoc.set_state( round( data[10]*256 + data[11], 1 ) )
			self.hcho.set_state(round( data[12]*256 + data[13], 1 ) )
			self.co2.set_state(round( data[16]*256 + data[17], 1 ) )
			# self.rssi.set(int(rssi))
		except IndexError:
			error("wp6003:update: invalid data")	

air_sensors = {}

