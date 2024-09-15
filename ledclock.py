#ledclock.py

from versions import versions
versions[__name__] = 3
# async version

import time
from core import offset_time, debug, started
from machine import Pin, RTC
from neopixel import NeoPixel
import uasyncio as asyncio
from rgblight import RGBlight
from flag import get

time_known = asyncio.Event()
# hand_index is a map to translate 0-12 to the starting led#

class LEDClock:
	def __init__(self, name, pin, num_leds, 
			  hand_index, direction_index, edge_index,
			min_hand_length, hour_hand_length, tail_length,
			face_rgb, hand_rgb, always_on=None ):
		self.leds = NeoPixel(Pin(pin), num_leds)
		# (400,850,800,350) - modified last value
		# timing=(350,800,800,350)  - from git issue #7985 to try
		# (250, 1000, 875, 375) FastLED
		self.leds.timing = (350,800,800,350)
		self.leds.fill((0,0,0))
		self.leds.write()
		# self.refresh = True
		# self.timer = Timer(-1)
		# self.timer.init(period=50, callback=self.refresh_leds)
		# Set color of outer edge leds or "None"
		self.face_rgb = face_rgb
		self.hand_rgb = hand_rgb
		self.mqtt_rgb = RGBlight(name)
		self.edge_index = edge_index
		self.hand_index = hand_index
		self.direction_index = direction_index
		self.mlen = min_hand_length
		self.hlen = hour_hand_length
		self.tail = tail_length
		self.always_on = always_on

		asyncio.create_task(self.handle_seconds())
		asyncio.create_task(self.handle_clock())
		asyncio.create_task(self.rgb_handler())
		#asyncio.create_task(self.flash_red())

	# # ISR to write leds
	# def refresh_leds(self, id):
	# 	if self.refresh:
	# 		self.leds.write()
	# 		self.refresh = False

	# merge led with new color, if 0 color, keep led color
	def merge_led(self, index, color):
		new = list(self.leds[index])
		for c in range(3):
			if color[c] > 0:
				new[c] = color[c]
		self.leds[index] = new
		return

	async def rgb_handler(self):
		async for _ , ev in self.mqtt_rgb.state.q:
			debug("rgb ev: {}, {}, {}".format(ev, self.mqtt_rgb.s_bri.state, self.mqtt_rgb.s_rgb.state))
			# trigger led update
			if ev == "ON":
				bri = int(self.mqtt_rgb.s_bri.state)
			else:
				bri = 0
				self.leds.fill((0,0,0))
				self.leds.write()
			#bri = int(s_bri.state)/255
			self.hand_rgb = ( bri, bri, bri )
			self.refresh_hands()
			
	def draw_hand(self,h,length,color,tail=0):
		for i in range(self.hand_index[h]-(self.direction_index[h]*tail),self.hand_index[h]+(self.direction_index[h]*length),self.direction_index[h]):
			self.merge_led(i, color)

	async def flash_red(self):
		# All red flashing at edges if lost time
		started("flash_red")
		while True:
			while get("timesynced"):
				await asyncio.sleep(2)
			debug("time not set!")
			for i in range(12):
				self.leds[self.edge_index[i]] = ( self.hand_rgb[0], 0, 0 )
			self.leds.write()
			await asyncio.sleep_ms(500)
			for i in range(12):
				self.leds[self.edge_index[i]] = ( 0, 0, 0 )
			self.leds.write()
			await asyncio.sleep_ms(500)

	async def handle_seconds(self):
		started("handle_seconds")
		lastsec = int(RTC().datetime()[6]/5)
		last_displayed = 0
		# Draw second hand
		while True:
			color = self.hand_rgb[2]
			if color == 0:
				await asyncio.sleep(1)
				continue
			sec = int(RTC().datetime()[6]/5)
			#if (last_displayed < 5 and last_displayed > sec) or last_displayed == sec or not get("timesynced"):
			if (last_displayed < 5 and last_displayed > sec) or last_displayed == sec:
				await asyncio.sleep_ms(100)
				continue
			last_displayed = sec
			delay = int(2000/color)
			for brighter in range(color):
				# fade out last second
				if brighter + 1 == color:
					index = self.edge_index[lastsec]
					self.leds[index] = (self.leds[index][0], self.leds[index][1], 0)
				else:
					self.merge_led(self.edge_index[lastsec], (0, 0, color - brighter - 1 ) )
				# fade in new second
				self.merge_led(self.edge_index[sec], (0, 0, brighter + 1))
				self.leds.write()
				await asyncio.sleep_ms(delay)
			lastled = self.edge_index[lastsec]
			# self.leds[lastled] = (self.leds[lastled][0], self.leds[lastled][1], self.face_rgb[2] )
			# self.merge_led(self.edge_index[sec], (0, 0, color) )
			# self.refresh=True
			lastsec = sec

	async def handle_clock(self):
		self.last_min = 0
		self.last_hour = 0
		self.next_hour = 1
		while True:
			ot = offset_time()
			minute = ot[4]
			if self.last_min == minute:
				await asyncio.sleep(1)
				continue
			# time to change min/hour
			hour = ot[3]
			if hour > 11:
				hour = hour - 12
			self.last_hour = hour
			self.next_hour = hour + 1
			if self.next_hour > 11:
				self.next_hour = 0
			self.last_min = minute
			self.refresh_hands()

	def refresh_hands(self):			
		if self.hand_rgb == (0,0,0):
			return
		self.leds.fill((0,0,0))
		for i in self.edge_index:
			self.leds[i] = self.face_rgb
			
		# draw minute hand
		self.draw_hand(int(self.last_min / 5), self.mlen, (0,self.hand_rgb[1],0), tail=self.tail )

		# Draw current/next hour hands, fade out/in as minute increases
		if self.hlen > 1:
			p = 1 - (self.last_min / 59)
			if p > 0 and self.last_min < 45:
				self.draw_hand(self.last_hour, self.hlen, tuple( int(x*y) for x, y in zip( (p,p,p), (self.hand_rgb[0],0,0) ) ), tail=self.tail )

			# calculate next hour to help fade in next hour hand as minute increases
			p = self.last_min / 59

			# Draw next hour hand and fade in as minute increases
			if p > 0 and self.last_min > 15:
				self.draw_hand(self.next_hour, self.hlen, tuple( int(x*y) for x, y in zip( (p,p,p), (self.hand_rgb[0],0,0) ) ), tail=self.tail )
		else:
			# always draw if just a dot, tail=0
			self.draw_hand(self.last_hour, self.hlen, (self.hand_rgb[0],0,0))

		# Center LED (bigclock only)
		if self.always_on:
			self.leds[self.always_on]= (self.hand_rgb[0],0,0)

		self.leds.write()
