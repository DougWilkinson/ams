# matrixclock.py

from versions import versions
versions[__name__] = 3
# 2,1,0: converted from modsensor

# text displayed based on values, not when sent from mqtt
from time import time, ticks_diff, ticks_ms, sleep_ms
from core import debug, info, error, offset_time
from flag import get
from random import getrandbits
from device import Device
from machine import Pin
from neopixel import NeoPixel
from hass import ha_setup
import uasyncio as asyncio

width=6
map=[40,41,42,43,44,45,46,47,39,38,37,36,35,34,33,32,24,25,26,27,28,29,30,31,23,22,21,20,19,18,17,16,8,9,10,11,12,13,14,15,7,6,5,4,3,2,1,0]

def convert_time(hour,minute):
	h = ' ' + str(hour)
	m = '0' + str(minute)
	return [ord(h[-2]), ord(h[-1]), 58, ord(m[-2]), ord(m[-1])]

def burst(leds, empty=6):
	leds[getrandbits(8)] = (getrandbits(1), getrandbits(1), getrandbits(1))
	for i in range(empty):
		leds[getrandbits(8)] = (0,0,0)
	leds.write()

class MatrixClock:
	
	def __init__(self, name, clock_color=(0,1,1), 
			  text_color=(0,0,1), pin=13, num_leds=255,
			  fade=120):
		self.leds = NeoPixel(Pin(pin), num_leds)
		self.setall()
		self.clock_color = clock_color
		self.warn_color = (1,0,0)
		self.text_color = text_color
		self.fade = fade
		self.text = Device(name + "_text", state='', notifier_setup=ha_setup)
		self.onoff = Device(name, state="ON", dtype="switch", notifier_setup=ha_setup)
		self.map = map
		self.width = width
		self.time_buffer = [32,32,32,32,32]
		self.digit_buffer = [(0,0,0)]*48
		self.textindex = -1
		self.fivesec = False
		self.lasthour = 0
		self.lastminute = 0
		self.colon = (0,0,0)
		self.show_display = True
		try:
			with open('matrix_font','rb') as f:
				self.font = f.read()
		except:
			error("Error reading font file!")
		
		asyncio.create_task(self.display_handler())
		asyncio.create_task(self.onoff_handler())
		asyncio.create_task(self.colon_handler())

	async def onoff_handler(self):
		async for _ , ev in self.onoff.q:
			debug("onoff: {}".format(ev) )
			if 'OFF' in ev:
				self.setall()
				self.show_display = False
			else:
				self.display_clock()
				self.show_display = True

	async def display_handler(self):
		while True:
			if self.show_display:
				if not get("timesynced"):
					self.display_clock(self.warn_color)
					await asyncio.sleep_ms(2000)
					continue
				currsec = offset_time()[5]
				if currsec == 1:
					self.display_clock(self.clock_color)
				if currsec == 54:
					self.display_clock(self.warn_color)
				if currsec == 20:
					self.display_text()
					self.display_clock(self.clock_color)
			await asyncio.sleep_ms(500)

		if second >= 54 or not get("timesynced"):
			debug("ledmatrix:clock: 5 sec warn")
			color = self.warn_color
		else:
			color = self.clock_color


	def setall(self, color=(0,0,0)):
		self.leds.fill(color)
		self.leds.write()

	def shiftdown(self, leds, digit):
		for col in range(3):
			for row in range(7):
				#even columns
				leds[digit*self.width*8 + col*16 + row] = leds[digit*self.width*8 + col*16 + 1 + row]
				#odd columns
				leds[digit*self.width *8 + col*16 + 15 - row] = leds[digit*self.width*8 + col*16 + 14 - row]

	def filldigit(self, buffer, color, ordnum=32, digit=0, buffrow=0, digitrow=0):
		#buffrow can be negative, c=col, r=row
		w = self.width
		achar = self.font[ordnum*6:ordnum*6+6]
		for c in range(w):
			for r in range(digitrow, 8-buffrow):
				if ( achar[c] & 1 << r):
					buffer[(digit * 8 * w) + self.map[r + buffrow - digitrow + (c*8)]] = color
				if not ( achar[c] & 1 << r):
					buffer[(digit * 8 * w) + self.map[r + buffrow - digitrow + (c*8)]] = (0,0,0)

	async def colon_handler(self):
		info("blink_colon: started")
		# 114,115,117,118,121,124 to make larger colon
		while True:
			self.leds[122] = self.colon
			self.leds[125] = self.colon
			self.leds.write()
			await asyncio.sleep(1)
			self.leds[122] = (0,0,0)
			self.leds[125] = (0,0,0)
			self.leds.write()
			await asyncio.sleep(1)

	def display_clock(self, color):
		debug("display_clock: triggered")
		ot = offset_time()
		hour = ot[3]
		minute = ot[4]
		second = ot[5]
		leds = self.leds		
		self.colon = color

		# update clock
		digits = convert_time(hour, minute)
		for d in range(4,-1,-1):
			#debug('clock: digit {}'.format(d) )
			if d == 2:
				continue

			# if self.time_buffer[4-d] != digits[4-d] or forceupdate:
			#debug(d, self.time_buffer, digits, ot, self.fivesec, color, tval)
			new = digits[4-d]
			for row in range(6,-1,-1):
				self.shiftdown(leds, d)
				self.filldigit(leds, color, ordnum=digits[4-d],digit=d, buffrow = 1, digitrow=row)
				leds.write()
				sleep_ms(self.fade)

			# if trans == "random":
			# 	if digits[4-d] != 32:
			# 		for i in range(5):
			# 			self.filldigit(leds, color, ordnum = 48+getrandbits(8) % 9, buffrow = 1, digit=d)
			# 			leds.write()
			# 			sleep_ms(fade)
			# 	self.filldigit(leds, color, ordnum=digits[4-d], buffrow = 1, digit=d)
			# 	leds.write()
			self.time_buffer[4-d] = digits[4-d]

	def display_text(self):
		if self.text.state == "":
			return
		leds = self.leds
		debug("display_text: triggered!")

		display = '    {}      '.format(self.text.state)
		index = 0
		color = self.text_color
		# shift left using buffer (single digit buffer 48 leds)
		lastshift = ticks_ms()
		while index < len(display):
			self.filldigit(self.digit_buffer, color, ord(display[index]), buffrow=1)
			# shift leds left 2 columns, then add 2 columns from sb (buffer)
			# loop 3 times each digit
			for s in range(2,-1,-1):
				# 256 - 16 = 240
				for t in range(240):
					leds[254-t] = leds[238-t]
				for t in range(16):
					leds[t] = self.digit_buffer[t+(16*s)]
				leds.write()
				fade_wait = ticks_diff(ticks_ms(), lastshift)
				lastshift = ticks_ms()
				if fade_wait < self.fade:
					sleep_ms( self.fade - fade_wait)
			index += 1

