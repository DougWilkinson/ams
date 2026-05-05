# matrixclock.py

from versions import versions
versions[__name__] = 12
# 10: converted to new device, profile and hass
# 11: added seconds bar to display
# 12: added alternating flip time and temperature

# text displayed based on values, not when sent from mqtt
from time import time, ticks_diff, ticks_ms, sleep_ms
from logger import debug, info, error
from localtime import offset_time
from events import time_synced
from random import getrandbits
from device import Device
from machine import Pin
from neopixel import NeoPixel
from system import exception_handler
import asyncio

#fakeimport matrix_font

width=6
map=[40,41,42,43,44,45,46,47,39,38,37,36,35,34,33,32,24,25,26,27,28,29,30,31,23,22,21,20,19,18,17,16,8,9,10,11,12,13,14,15,7,6,5,4,3,2,1,0]
seconds_map = [240,239,224,223,208,207,192,191,176,175,160,159,144,143,128,127,112,111,96,95,80,79,64,63,48,47,32,31,16,15]

def convert_time(hour,minute):
	h = ' ' + str(hour)
	m = '0' + str(minute)
	return [ord(h[-2]), ord(h[-1]), 32, ord(m[-2]), ord(m[-1])]

def burst(leds, empty=6):
	leds[getrandbits(8)] = (getrandbits(1), getrandbits(1), getrandbits(1))
	for i in range(empty):
		leds[getrandbits(8)] = (0,0,0)
	leds.write()

class MatrixClock:
	
	def __init__(self, name, clock_color=(0,1,1), 
			  text_color=(0,0,1), pin=13, num_leds=255,
			  fade=60):
		self.leds = NeoPixel(Pin(pin), num_leds)
		self.setall()
		self.clock_color = clock_color
		self.warn_color = (1,0,0)
		self.text_color = text_color
		self.fade = fade
		self.text = Device(name + "_text", state='hello world!!')
		
		# self.render_text_buffer() uses this to store text for sliding
		# enough for 30 characters of text (48 * 50 =  2400)
		self.text_buffer = [(0,0,0)]*2400
		self.text_buffer_size = 0		
		
		self.onoff = Device(name, state="ON", dtype="switch")
		self.map = map
		self.width = width
		self.time_buffer = [32,32,32,32,32]
		self.digit_buffer = [(0,0,0)]*48
		
		self.textindex = -1
		self.fivesec = False
		self.lasthour = 0
		self.lastminute = 0
		self.colon = (0,0,0)
		
		self.show_display = asyncio.Event()
		self.show_display.set()

		self.show_colon = asyncio.Event()
		self.show_colon.set()

		self.colon_off = asyncio.Event()
		self.colon_off.set()

		try:
			with open('matrix_font','rb') as f:
				self.font = f.read()
		except:
			error("Error reading font file!")

		# default schedule red clock at 55 seconds
		# self.schedule = {'15': {'function': self.display_vertical_text, 'color': self.text_color},
		# 		'30': {'function': self.display_time, 'color': self.clock_color},
		# 		'45': {'function': self.display_vertical_text, 'color': self.text_color},
		# 		'55': {'function': self.display_time, 'color': self.warn_color}
		# 		}
		
		asyncio.create_task(self.display_handler())
		asyncio.create_task(self.onoff_handler())
		# asyncio.create_task(self.colon_handler())
		# asyncio.create_task(self.seconds_bar_handler())

	@exception_handler
	async def onoff_handler(self):
		async for _ , ev in self.onoff.q:
			debug("onoff: {}".format(ev) )
			if 'OFF' in ev:
				self.setall()
				self.show_display.clear()
			else:
				#await self.colon_off.wait() 
				self.show_display.set()

	def render_text_buffer(self):
		# limit to first 30 characters of text
		text = f'     {self.text.state[0:30]}     '
		self.text_buffer_size = len(text) * 48
		buffer_index = len(text) - 1
		for digit in text:
			self.filldigit(self.text_buffer, self.text_color, ord(digit), digit=buffer_index, buffrow=1)
			buffer_index -= 1

	@exception_handler
	async def display_handler(self):

		self.render_text_buffer()
		text_index = self.text_buffer_size - 256
		last_text = self.text.state
		
		while True:

			# wait for display to be on
			await self.show_display.wait()	

			# clear leds and add time
			self.leds.fill((0,0,0))
			self.update_time_leds()

			# merge leds with text color
			for t in range(255):
				# merge colors
				lc = self.leds[t]
				tc = self.text_buffer[t+text_index]
				self.leds[t] = (tc[0]+lc[0], tc[1]+lc[1], tc[2]+lc[2])
			
			# update leds and wait
			self.leds.write()
			await asyncio.sleep_ms(self.fade)

			# shift index by two columns
			text_index -= 16
			if text_index < 0:
				if last_text != self.text.state:
					self.render_text_buffer()
					last_text = self.text.state
				text_index = self.text_buffer_size - 256

			

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

	# fill digit buffer with single digit or character
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


	# @exception_handler
	# async def colon_handler(self):
	# 	info("blink_colon: started")
	# 	# 114,115,117,118,121,124 to make larger colon
	# 	while True:
	# 		await self.show_colon.wait()
			
	# 		# colon on
	# 		self.leds[122] = self.colon
	# 		self.leds[125] = self.colon
	# 		#self.leds.write()
	# 		self.colon_off.clear()
	# 		await asyncio.sleep(1)

	# 		# colon off
	# 		self.leds[122] = (0,0,0)
	# 		self.leds[125] = (0,0,0)
	# 		#self.leds.write()
	# 		self.colon_off.set()
	# 		await asyncio.sleep(1)

	# push current time to leds (no write)
	def update_time_leds(self):

		if not time_synced.is_set():
			color = self.warn_color
		else:
			color = self.clock_color

		ot = offset_time()
		hour = ot[3]
		minute = ot[4]
		second = ot[5]
		#debug("display_time: {}:{} {}".format(hour, minute, color) )

		# update display with current time
		digit_ordinals = convert_time(hour, minute)

		for d in range(4,-1,-1):
			# render time digits
			self.filldigit(self.leds, color, ordnum=digit_ordinals[4-d],digit=d, buffrow = 1, digitrow=0)

		if second % 2 == 0:
			# colon on
			self.leds[122] = color
			self.leds[125] = color

		else:
			# colon off
			self.leds[122] = (0,0,0)
			self.leds[125] = (0,0,0)


	def display_vertical_text(self, color):
		if self.text.state == "":
			return
		text_ordinals_list = [ord(c) for c in self.text.state]
		
		# display first 5 characters
		self.show_colon.clear()
		self.display(text_ordinals_list[0:5], color)


	def display_horizontal_text(self):
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

