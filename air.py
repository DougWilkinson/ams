#air.py

version = (2,0,7)
# async version

from core import debug, info, error
from device import Device
from hass import ha_setup

class WP6003:

	oui = '600303'
	uuid = 0xFFF1
	write_value = 171

	def __init__(self, mac):
		self.mac = mac

		name = "wp6003_" + mac + "_"
		self.temp = Device(name + "temperature", 
							"0",
							units = 'F',
							notifier_setup=ha_setup,
							publish=False)
		self.tvoc = Device(name + "TVOC", 
							"0", 
							units = "mg/m3",
							notifier_setup=ha_setup,
							publish=False)
		self.hcho = Device(name + "HCHO", 
							"0", 
							units = "mg/m3",
							notifier_setup=ha_setup,
							publish=False)
		self.co2 = Device(name + "CO2", 
							"0", 
							units = "ppm",
							notifier_setup=ha_setup,
							publish=False)

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

