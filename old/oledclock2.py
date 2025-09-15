# oledclock.py

version = 2
# display device with json formatted objects
# name: {x,y,color,name,text}
# 2: UTC support and random wait

from machine import Pin, SoftI2C, SPI
from time import sleep, ticks_ms
import framebuf
import array
import math
import json
from random import randint
import ssd1306

defaults = { "ssd1306": { "scl": 22, "sda": 21, "effect": "centered", "hand": 3,
						"width": 128, "height": 64, "radius": 30, "color" : 1 },
			"sh1106": { "scl": 22, "sda": 21, "effect": "centered", "hand": 3,
	      				"width": 128, "height": 64, "radius": 25, "color" : 1 },
			"ilismall": { "baudrate": 4000000, "effect": "floating", "hand": 3,
						"width": 102, "height": 102, "radius": 45, "color" : 63488  },
			"ili9341p": { "baudrate": 8888888, "effect": "centered", "hand": 5,
						"width": 240, "height": 320, "radius": 100, "color" : 31  },
			"oled": "ili9341p",
			"rotate": 0
			}

class Class:
	
	def __init__(self, ssd_i2c, width=128, height=64, 
			effect="centered", hand=3, radius=30, color=1):
		modconfig = defaults
		specs = defaults[self.type]
		self.width = width
		self.height = height
		self.hand = hand
		self.color = color
		self.clock_radius = radius
		self.effect = effect
		# self.weather = Device("hass/weather", "subscriber", "updating...", prepend_name=False, update_mqtt=False, use_haconfig=False)
		# self.outside_temp = Device("hass/temp/outside", "subscriber", "--`F", prepend_name=False, update_mqtt=False, use_haconfig=False)
		self.text = None
		self.xdir = 1
		self.ydir = 1
		self.last_second = 0
		self.last_minute = 0
		self.last_hour = 0
		self.lminute = [[0,0]]*5
		self.lhour = [[0,0]]*5
		self.lsec = [[0,0]]*5
		self.face = False

		self.oled = ssd1306.SSD1306_I2C(self.width, self.height, ssd_i2c)

	def getxy(self, angle, radius):
		x = round(radius * math.sin(math.radians(angle)))
		y = round(radius * math.cos(math.radians(angle)))
		return array.array('h',[x,-y])
		
	def draw_hand(self, last, angle, cx, cy, fraction=1.0, width=0, color=0):

		# only draw line and don't return last
		if width == 0:
			if angle == last[4]:
				return last
			longhand = self.getxy(angle, * fraction)
			#print(last, cx,cy,longhand)
			self.oled.draw_line(cx-int(longhand[0]*.1), cy-int(longhand[1]*.1), cx+longhand[0], cy+longhand[1], color)
			self.oled.draw_line(cx - int(last[2][0]*.1), cy-int(last[2][1]*.1), cx+last[2][0], cy+last[2][1], 0)
			return [0,0, longhand, 0, angle]
		
		if angle == last[4]:
			self.oled.poly(cx,cy,array.array('h',last[0] + last[1] + last[2]), color, False)
			self.oled.poly(cx,cy,array.array('h',last[0] + last[1] + last[3]), color, True)
			return last

		start = ticks_ms()
		pbase = self.getxy(angle+90, width)
		nbase = self.getxy(angle-90, width)
		longside = self.getxy(angle, self.clock_radius*fraction)
		shortside = self.getxy(angle+180, self.clock_radius * 0.2)
		# print("calc: ", ticks_ms() - start)
		start = ticks_ms()
		# Draw long side (outline)
		self.oled.poly(cx,cy,array.array('h',pbase + nbase + longside), color, False)
		self.oled.poly(cx,cy,array.array('h',last[0] + last[1] + last[2]), 0, False)
		# print("long: ", ticks_ms() - start)
		start = ticks_ms()

		# Draw short side (filled in)
		self.oled.poly(cx,cy,array.array('h',pbase + nbase + shortside), color, True)
		self.oled.poly(cx,cy,array.array('h',last[0] + last[1] + last[3]), 0, True)
		# print("short: ", ticks_ms() - start)

		return [pbase, nbase, longside, shortside, angle]
	
			# self.oled.poly(cx,cy,array.array('h',[-2,-2,2,2,x,-y]),color,1)
			# self.oled.poly(cx,cy,array.array('h',[-2,2,2,-2,x,-y]),color,1)
			# self.oled.poly(cx,cy,array.array('h',[0,2,0,-2,x,-y]),color,1)
			# self.oled.poly(cx,cy,array.array('h',[-2,0,2,0,x,-y]),color,1)

	def draw_text(self):
		text = json.loads(self.text.value)
		for name, content in text.items():
			self.oled.fill_hrect(content['x'], content['y'], self.width, content['y'] + self.font.height, 0)
			self.oled.draw_text(content['x'], content['y'], content['text'], self.font, content['color'])

	def draw_face(self, cx,cy,color=0):
		self.oled.clear()
		# self.oled.draw_text(239-(len(self.outside_temp.value )*18), 0, str(self.outside_temp.value), self.lucida, 63488)
		# self.oled.draw_text(0, 291, self.weather.value, self.lucida, 63488)
		self.draw_text()
		for i in range(12):
			self.oled.ellipse(cx + round(self.clock_radius * math.sin(math.radians(i*30))),
		    				cy + round(self.clock_radius * math.cos(math.radians(i*30)) ),
							self.hand-1, self.hand-1, color, color)

	def update(self):
		# if self.clock_radius.mqtt_received or self.weather.mqtt_received or self.outside_temp.mqtt_received:
		if self.clock_radius.mqtt_received:
			self.face = False
			# self.weather.mqtt_received = False
			# self.outside_temp.mqtt_received = False
			self.clock_radius.mqtt_received = False
			self.lminute = [[0,0]]*5
			self.lhour = [[0,0]]*5
			self.lsec = [[0,0]]*5

		if 'timezone' in eventbus:
			ot = offset_time()
			hour = ot[3]
			minute = ot[4]
			second = ot[5]
		else:
			hour = randint(0,11)
			minute = randint(0,59)
			second = randint(0,59)

		# 24 hour time to 12
		if hour > 11:
			hour = hour - 12

		cx = self.width >> 1
		cy = self.height >> 1

		# erase last face/hands
		# if self.lsec != second or self.lminute != minute or self.lhour != hour:
		# 	self.oled.fill(0)
		# if self.effect == "floating":
		# 	self.draw_face(cx,cy)
		# if self.lminute != minute or self.lhour != hour:
		# 	self.draw_hand(self.lminute * 6, cx, cy, fraction=0.9, width=self.hand)
		# 	angle = 30 * self.lhour + round((self.lminute/60) * 30)
		# 	self.draw_hand(angle, cx, cy, fraction = 0.6, width=self.hand)
		# if self.lsec != second:	
		# 	self.draw_hand(self.lsec * 6, cx, cy, fraction=0.8)

		if self.effect == "grow":
			if (hour > 9 or hour < 3) and (minute > 49 or minute < 11):
				cy = 60
				
			if (hour > 3 and hour < 9) and (minute > 19 and minute < 41):
				cy = 4
		
		if not self.face:
			self.draw_face(cx, cy, self.color)
			self.face = True

		# Second hand (line)
		if self.lsec[4] != second*6:
			self.lsec = self.draw_hand(self.lsec, second * 6, cx, cy, fraction=0.8, color=self.color)

			# Minute hand
			self.lminute = self.draw_hand(self.lminute, minute * 6, cx, cy, fraction=0.9, width=self.hand, color=self.color)

			#Hour hand
			angle = 30 * hour + round((minute/60) * 30)
			self.lhour = self.draw_hand(self.lhour, angle, cx, cy, fraction = 0.6, width=self.hand, color=self.color)

		if self.effect == 'floating':
			self.oled.x_zero = self.oled.x_zero + self.xdir
			if self.oled.x_zero > (self.oled.display.width - 1 - self.width) or self.oled.x_zero < 1:
				self.xdir = - self.xdir
			self.oled.y_zero = self.oled.y_zero + self.ydir
			if self.oled.y_zero > (self.oled.display.height - 1 - self.height) or self.oled.y_zero < 1:
				self.ydir = - self.ydir

		self.oled.show()
		if self.text.mqtt_received:
			self.text.mqtt_received = False
			self.draw_text()

