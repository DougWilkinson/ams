# lixieclock.py

from versions import versions
versions[__name__] = 3

from time import time, sleep_ms
from random import getrandbits
from device import Device
from neopixel import NeoPixel

from core import offset_time, error, debug, started
from machine import Pin, RTC
import uasyncio as asyncio
from flag import get
from machine import Timer
from hass import ha_setup

time_known = asyncio.Event()

digit_map = [3, 4, 2, 0, 8, 6, 5, 7, 9, 1]
next_digit = [2,0,9,8,7,6,1,5,4,3,2,0,9,8,7,6,1,5,4,3] # start 111 end 566
prev_digit = [1,1,0,9,8,7,5,4,3,2]

def mod_color(color, percent):
	percent = percent/100
	return (int(color[0] * percent), int(color[1] * percent), int(color[2] * percent) )

def split_digit(value):
	ones = value % 10
	return int( (value - ones) / 10), ones

def all_off(leds):
	leds.fill((0,0,0))
	leds.write()

class LixieClock:
	
	def __init__(self, name, min_pin=4, hour_pin=13, flip_delay=60, fade_step=1,
			  color=(192,24,0) ):
		# mled has two leds at end of string for colon
		self.mled = NeoPixel(Pin(min_pin), 43)
		self.hled = NeoPixel(Pin(hour_pin), 41)
		self.color = color
		# delay for flip mode (msec)
		self.flip_delay = flip_delay
		# fade step (higher value for faster fade in/out)
		# 1 is the slowest, 100 is instant on
		self.fade_step = fade_step
		self.fivesec = False
		self.last = [4,0,4,0]
		self.transition = Device(name + "_transition", state="fade", notifier_setup=ha_setup)
		self.mode = Device(name + "_mode", state="clock12", notifier_setup=ha_setup)
		self.onoff = Device(name, state="ON", dtype="switch", notifier_setup=ha_setup)
		self.colon = False
		all_off(self.mled)
		all_off(self.hled)
		
		self.last_min = 42
		self.next_min = 42
		self.last_hour = 42
		self.next_hour = 42

		asyncio.create_task(self.handle_clock())
		asyncio.create_task(self.handle_colon())
		asyncio.create_task(self.flash_time())
		asyncio.create_task(self.mode_handler())
		asyncio.create_task(self.onoff_handler())
		asyncio.create_task(self.transition_handler())

	async def onoff_handler(self):
		async for _ , ev in self.onoff.q:
			debug("onoff: {}".format(ev) )
			if 'OFF' in ev:
				all_off(self.mled)
				all_off(self.hled)
			else:
				self.refresh_hands()

	async def mode_handler(self):
		async for _ , ev in self.mode.q:
			debug("mode: {}".format(ev) )
			self.refresh_hands()

	async def transition_handler(self):
		async for _ , ev in self.transition.q:
			debug("transition: {}".format(ev) )
			self.refresh_hands()

	async def flash_time(self):
		# Signals that time is not set
		started("flash_time")
		while True:
			while get("timesynced"):
				await asyncio.sleep(2)
			error("time not synced!")
			time_known.clear()
			self.fade_step = 5
			saved_delay = self.flip_delay
			while not get("timesynced"):
				self.refresh_hands()
				await asyncio.sleep_ms(200)
			error("time synced!")
			self.flip_delay = saved_delay
			self.fade_step = 1
			time_known.set()

	def write_digit(self, value, place, color):
		zplace = (place == 0)
		if place < 2:
			led = self.hled
		else:
			led = self.mled
		if place == 0 or place == 2:
			place = 20
		else:
			place = 0
		for i in range(place, place+20):
			led[i] = (0,0,0)
		if not zplace or value != 0 or (self.mode and self.mode.state != "clock12"):
			led[digit_map[value] + place] = color
			led[digit_map[value] + place + 10] = color
		led.write()

	# value is a list with h,h,m,m
	# color is a set ()
	# Call write_digit for each with color value
	def show_time(self, value, color):
		for i in range(4):
			self.write_digit(value[i], i, color)

	def show_colon(self, brightness):
		mc = mod_color( self.color, 0.25 * brightness )
		self.mled[40] = mc
		self.mled[41] = mc
		self.mled.write()

	async def handle_colon(self):
		while True:
			await time_known.wait()
			self.colon = False
			for brightness in range(20, 0, -self.fade_step):
				self.show_colon(brightness)
				sleep_ms(25)
			await asyncio.sleep_ms(500)
			self.colon = True
			for brightness in range(0, 21, self.fade_step):
				self.show_colon(brightness)
				sleep_ms(25)	
			await asyncio.sleep_ms(500)

	async def handle_clock(self):
		while True:
			ot = offset_time()
			self.next_min = ot[4]
			if self.last_min == self.next_min:
				await asyncio.sleep(1)
				continue
			while self.colon:
				await asyncio.sleep_ms(100)
			# time to change min/hour
			hour = ot[3]
			if self.mode and self.mode.state == 'clock12':
				if hour > 12:
					hour = hour - 12
			self.next_hour = hour
			self.refresh_hands()
			self.last_min = self.next_min
			self.last_hour = self.next_hour


	def refresh_hands(self):
		if self.onoff.state != "ON":
			return

		# now is time to change display to
		now = [0,0,0,0]
		now[0], now[1] = split_digit(self.next_hour)
		# minute
		now[2], now[3] = split_digit(self.next_min)

		# tmp is last displayed time
		tmp = [0,0,0,0]
		tmp[0], tmp[1] = split_digit(self.last_hour)
		tmp[2], tmp[3] = split_digit(self.last_min)

		if self.transition and self.transition.state == "fade":
			for brightness in range(100, 0, -self.fade_step):
				self.show_time(tmp, mod_color(self.color, brightness) )
				# if self.colon and brightness < 20:
				# 	mc = mod_color( self.color, 0.25 * brightness )
				# 	self.mled[40] = mc
				# 	self.mled[41] = mc
				# 	self.mled.write()
					
			for brightness in range(0, 101, self.fade_step):
				self.show_time(now, mod_color(self.color, brightness) )
				# if self.colon and brightness > 80:
				# 	mc = mod_color( self.color, 0.25 * (brightness-80) )
				# 	self.mled[40] = mc
				# 	self.mled[41] = mc
				# 	self.mled.write()
		
		if self.transition and self.transition.state == "flip":
			
			for i in range(4):
				if i == 0 and now[i] == 0 and tmp[i] == 0:
					continue
				tmp[i] = next_digit[tmp[i]]
				skip_first = True
				while tmp[i] != now[i] or skip_first:
					skip_first = False
					# step in
					tmp[i] = next_digit[tmp[i]]
					self.show_time(tmp, self.color )
					sleep_ms(self.flip_delay)

			# # set colon to 5%
			# mc = mod_color(self.color,5)
			# self.mled[40] = mc
			# self.mled[41] = mc
			# self.mled.write()

