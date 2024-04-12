# ledstatus.py

version = (1,0,3)

from machine import Pin
from time import ticks_ms, ticks_diff, sleep_ms
#from alog import info, debug, error, started, stopped, exited
#import asyncio
from device import Device
#from hass import ha_setup
from neopixel import NeoPixel

# Show led colors based on device.state:
# good = pulsing green
# needed = flashing red
# unknown = flashing purple

class LEDStatus:
	def __init__(self, status_device, pin=15, num_leds=3, brightness=50 ):
		self.status = status_device
		#started(self.status.name)
		self.brightness = brightness
		self.num = num_leds
		self.leds = NeoPixel(Pin(pin), num_leds)
		#self.fill()
		# self.status = Device(self.name, "unknown", dtype="sensor", notifier=ha_setup)
		self.last = ticks_ms()
		#asyncio.create_task(self.update())		

	def fill(self, color=(0,0,0) ):
		self.leds.fill(color)
		self.leds.write()

	def update(self, delay=100):
		while True:
			pulse = ticks_diff(ticks_ms(), self.last)
			if pulse > 500:
				pulse = 500
				self.last = ticks_ms()
			# sweeps range of brightness (default 30) 
			pulse = abs(int((self.brightness*2) * (pulse/500)) - self.brightness)
			pulse = 0 if pulse < 0 else pulse
			npulse = self.brightness - pulse
			npulse = 0 if npulse < 0 else npulse
			# Purple pulse - Invalid/Init state
			self.leds[0] = [npulse >> 1,0,pulse >> 1 ]
			self.leds[1] = [npulse >> 1,0,pulse >> 1 ]
			if self.status.state == "good":
				self.leds[0] = [0,int(self.brightness/3),0]
				self.leds[1] = [0,int(self.brightness/3),0]
			if self.status.state == "needed":
				self.leds[0] = [pulse,0,0]
				self.leds[1] = [pulse,0,0]
			# if self.status.value == "unknown":
			# 	self.leds[0] = [pulse >> 1,0,npulse >> 1]
			# 	self.leds[1] = [npulse >> 1,0,pulse >> 1]
			self.leds.write()
			sleep_ms(delay)
from device import Device
from ledstatus import LEDStatus
d=Device("status", "unknown", dtype="sensor")
l=LEDStatus(status_device=d)
