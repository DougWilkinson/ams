# fbclock.py
# framebuffer based analog clock

from versions import versions
versions[__name__] = 3
# 200: async version with oled type in params

from time import sleep_ms, ticks_ms
from machine import RTC
import array
import math
import json
import uasyncio as asyncio
from core import debug, offset_time
from random import randint

class FBClock:
	
	# display would be something like ili9341fb that uses FrameBuffer
	# requires clear, ellipse, rect
	def __init__(self, display, color=31, radius=100, text=None, font=None, hand=5, effect="centered" ):
		self.display = display
		self.text = text
		self.font = font
		self.hand = hand
		self.color = color
		self.clock_radius = radius
		self.effect = effect
		self.xdir = 1
		self.ydir = 1
		self.last_second = 0
		self.last_minute = 0
		self.last_hour = 0
		self.lminute = [[0,0]]*5
		self.lhour = [[0,0]]*5
		self.lsec = [[0,0]]*5
		self.face = False
		self.seconds_color = 63488
		asyncio.create_task(self.clock_handler())
		asyncio.create_task(self.text_handler())

	def getxy(self, angle, radius):
		x = round(radius * math.sin(math.radians(angle)))
		y = round(radius * math.cos(math.radians(angle)))
		return array.array('h',[x,-y])
		
	def draw_hand(self, last, angle, cx, cy, fraction=1.0, width=0, color=0):

		# only draw line and don't return last
		# if width == 0:
		# 	if angle == last[4]:
		# 		return last
		# 	longhand = self.getxy(angle,self.clock_radius * fraction)
		# 	#print(last, cx,cy,longhand)
		# 	self.display.draw_line(cx-int(longhand[0]*.1), cy-int(longhand[1]*.1), cx+longhand[0], cy+longhand[1], color)
		# 	self.display.draw_line(cx - int(last[2][0]*.1), cy-int(last[2][1]*.1), cx+last[2][0], cy+last[2][1], 0)
		# 	return [0,0, longhand, 0, angle]
		
		if angle == last[4]:
			self.display.poly(cx,cy,array.array('h',last[0] + last[1] + last[2]), color, False)
			self.display.poly(cx,cy,array.array('h',last[0] + last[1] + last[3]), color, True)
			return last

		start = ticks_ms()
		pbase = self.getxy(angle+90, width)
		nbase = self.getxy(angle-90, width)
		longside = self.getxy(angle, self.clock_radius*fraction)
		shortside = self.getxy(angle+180, self.clock_radius * 0.2)
		# print("calc: ", ticks_ms() - start)
		start = ticks_ms()
		# Draw long side (outline)
		self.display.poly(cx,cy,array.array('h',last[0] + last[1] + last[2]), 0, False)
		self.display.poly(cx,cy,array.array('h',pbase + nbase + longside), color, False)
		# print("long: ", ticks_ms() - start)
		start = ticks_ms()

		# Draw short side (filled in)
		self.display.poly(cx,cy,array.array('h',last[0] + last[1] + last[3]), 0, True)
		self.display.poly(cx,cy,array.array('h',pbase + nbase + shortside), color, True)
		# print("short: ", ticks_ms() - start)

		return [pbase, nbase, longside, shortside, angle]
	
			# self.display.poly(cx,cy,array.array('h',[-2,-2,2,2,x,-y]),color,1)
			# self.display.poly(cx,cy,array.array('h',[-2,2,2,-2,x,-y]),color,1)
			# self.display.poly(cx,cy,array.array('h',[0,2,0,-2,x,-y]),color,1)
			# self.display.poly(cx,cy,array.array('h',[-2,0,2,0,x,-y]),color,1)

	def draw_face(self, cx,cy,color=0):
		self.display.clear()
		# self.display.draw_text(239-(len(self.outside_temp.value )*18), 0, str(self.outside_temp.value), self.lucida, 63488)
		# self.display.draw_text(0, 291, self.weather.value, self.lucida, 63488)
		#self.draw_text()
		for i in range(12):
			self.display.ellipse(cx + round(self.clock_radius * math.sin(math.radians(i*30))),
		    				cy + round(self.clock_radius * math.cos(math.radians(i*30)) ),
							self.hand-1, self.hand-1, color, color)

	def draw_seconds(self, seconds, cx, cy):
		if seconds == 0:
			self.seconds_color = 63488 - self.seconds_color
		start = self.getxy(seconds*6, self.clock_radius-self.hand)
		if seconds == 59:
			seconds = 0
		end = self.getxy((seconds+1)*6, self.clock_radius-self.hand)
		self.display.draw_line(cx+start[0], cy+start[1], cx+end[0], cy+end[1], self.seconds_color)

	async def text_handler(self):
		async for _ , ev in self.text.q:
			debug("state ev: {}".format(ev))
			text = json.loads(self.text.state)
			for name, content in text.items():
				self.display.fill_hrect(content['x'], content['y'], self.display.width, content['y'] + self.font.height, 0)
				self.display.draw_text(content['x'], content['y'], content['text'], self.font, content['color'])


	async def clock_handler(self):
		cx = self.display.width >> 1
		cy = self.display.height >> 1
		self.draw_face(cx, cy, self.color)
		while True:
			start = ticks_ms()
			ot = offset_time()
			hour = ot[3]
			minute = ot[4]
			second = ot[5]

			# 24 hour time to 12
			if hour > 11:
				hour = hour - 12

			if self.effect == "grow":
				if (hour > 9 or hour < 3) and (minute > 49 or minute < 11):
					cy = 60
					
				if (hour > 3 and hour < 9) and (minute > 19 and minute < 41):
					cy = 4
			
			if self.lminute[4] != minute*6:
				# Minute hand
				self.lminute = self.draw_hand(self.lminute, minute * 6, cx, cy, fraction=0.9, width=self.hand, color=self.color)

				#Hour hand
				angle = 30 * hour + round((minute/60) * 30)
				self.lhour = self.draw_hand(self.lhour, angle, cx, cy, fraction = 0.6, width=self.hand, color=self.color)

			# self.lsec = self.draw_hand(self.lsec, second * 6, cx, cy, fraction=0.8, color=self.color)
			self.draw_seconds(second, cx, cy)

			if self.effect == 'floating':
				self.display.x_zero = self.display.x_zero + self.xdir
				if self.display.x_zero > (self.display.display.width - 1 - self.display.width) or self.display.x_zero < 1:
					self.xdir = - self.xdir
				self.display.y_zero = self.display.y_zero + self.ydir
				if self.display.y_zero > (self.display.display.height - 1 - self.display.height) or self.display.y_zero < 1:
					self.ydir = - self.ydir

			self.display.show()
			remaining = ticks_ms()-start
			if remaining > 0:
				await asyncio.sleep_ms(remaining)
