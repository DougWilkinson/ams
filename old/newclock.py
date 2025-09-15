# cp_clock.py

from time import sleep, localtime
from adafruit_ticks import ticks_ms
from rtc import RTC
#import adafruit_framebuf as framebuf
import math

import board
import busio
import microcontroller
import terminalio
import displayio
from adafruit_display_text import label
import adafruit_ili9341
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.polygon import Polygon
from adafruit_display_shapes.triangle import Triangle

import adafruit_connection_manager
import adafruit_ntp
import wifi
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=8, cache_seconds=120)

from fourwire import FourWire

# Release any resources currently in use for the displays
displayio.release_displays()

# D1 mini using esp32-s2
# spi = busio.SPI(clock=board.D36, MOSI=board.D35, MISO=board.D37)
# tft_cs = microcontroller.pin.GPIO34
# tft_dc = microcontroller.pin.GPIO38
# display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D6)

# esp32-s3 devkit
spi = busio.SPI(clock=board.GPIO6, MOSI=board.GPIO11, MISO=board.GPIO10)
tft_cs = microcontroller.pin.GPIO7
tft_dc = microcontroller.pin.GPIO5
display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.GPIO4)

display = adafruit_ili9341.ILI9341(display_bus, width=240, height=320, rotation=270)
display.auto_refresh = False
splash = displayio.Group()
display.root_group = splash

class Clock:
	
	def __init__(self, color=0x0000FF, radius=100 ):
		self.width = 240
		self.height = 320
		self.cx = self.width >> 1
		self.cy = self.height >> 1
		self.hand = 5
		self.color = color
		self.clock_radius = radius
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
		# asyncio.create_task(self.text_handler())
		splash.append(self.gen_face())
		# hours, min, secs
		splash.append(displayio.Group())
		splash.append(displayio.Group())
		splash.append(displayio.Group())
		splash.append(displayio.Group())

	def getxy(self, angle, radius):
		x = self.cx + round(radius * math.sin(math.radians(angle)))
		y = self.cy - round(radius * math.cos(math.radians(angle)))
		return ( x,y )
		
	def gen_hand(self, angle, fraction=1.0, width=0):
		hand = displayio.Group()
		# if angle == last[4]:
		# 	splash.append(Polygon(points=[(cx,cy), last[0], last[1], last[2] ], outline=255, close=True, colors=1) )
		# 	splash.append(Polygon(points=[(cx,cy), last[0], last[1], last[3] ], outline=255, close=True, colors=1) )
		# 	# Polygon(cx,cy,array.array('h',last[0] + last[1] + last[2]), color, False)
		# 	# Polygon(cx,cy,array.array('h',last[0] + last[1] + last[3]), color, True)
		# 	return last

		x0, y0 = self.getxy(angle+90, width)
		x2, y2 = self.getxy(angle-90, width)
		lx, ly = self.getxy(angle, self.clock_radius*fraction)
		sx, sy = self.getxy(angle+180, self.clock_radius * 0.2)
		#print(width, angle, pbase, nbase, longside, shortside)

		# print("calc: ", ticks_ms() - start)
		# Erase last long side (outline)
		#hand.append(Polygon(points=[(cx,cy), last[0], last[1], last[2] ], outline=0, close=True, colors=1) )
		
		# Draw new long side (outline)
		# hand.append(Polygon(points=[pbase , longside, nbase ], outline=255, close=True) )
		
		# Polygon(cx,cy,array.array('h',pbase + nbase + longside), color, False)
		# print("long: ", ticks_ms() - start)

		# Draw short side (filled in)
		# Erase last short side (outline)
		#hand.append(Polygon(points=[(cx,cy), last[0], last[1], last[3] ], outline=0, close=True, colors=1) )
		
		# Draw new short side (outline)
		# x0, y0 = pbase
		# sx1, sy1 = shortside
		# lx1, ly1 = longside
		# x2, y2 = nbase

		# short side (filled)
		hand.append(Triangle(x0=x0, y0=y0, x1=sx, y1=sy, x2=x2, y2=y2, fill=255, outline=255) )

		# long side (outline)
		hand.append(Triangle(x0=x0, y0=y0, x1=lx, y1=ly, x2=x2, y2=y2, fill=0, outline=255) )

		#Polygon(cx,cy,array.array('h',last[0] + last[1] + last[3]), 0, True)
		#Polygon(cx,cy,array.array('h',pbase + nbase + shortside), color, True)
		
		# print("short: ", ticks_ms() - start)

		#return [pbase, nbase, longside, shortside, angle]
		return hand
	
	def gen_face(self):
		cx = self.width >> 1
		cy = self.height >> 1
		face = displayio.Group()
		for i in range(12):
			face.append(Circle(x0=cx + round(self.clock_radius * math.sin(math.radians(i*30))),
		    				y0=cy + round(self.clock_radius * math.cos(math.radians(i*30)) ),
							r=self.hand-1, fill=self.color, outline=self.color, stroke=1) )
		return face

	def draw_all_hands(self, cx, cy, second_angle, second, minute, hour ):
			angle_hour = 30 * hour + round((minute/60) * 30)
			angle_minute = 6 * minute + round((second/60) * 6)
			splash[1] = self.gen_hand(angle_hour, cx, cy, fraction = 0.6, width=self.hand, color=self.color)
			splash[2] = self.gen_hand(angle_minute, cx, cy, fraction=0.9, width=self.hand, color=self.color)
			splash[3] = self.gen_hand(second_angle, cx, cy, fraction=0.8, color=self.color)
			display.refresh()
			#self.oled.show()

	def gen_digital(self, h,m,s):
		text_group = displayio.Group(scale=3, x=53, y=300)
		text = "{}:{:0>2}:{:0>2}".format(h,m,s)
		text_area = label.Label(terminalio.FONT, text=text, color=0x00FFFF)
		text_group.append(text_area)  # Subgroup for text scaling
		return text_group


	def update(self):
		cx = self.width >> 1
		cy = self.height >> 1
		last_angle_hour = 0
		last_angle_min = 0
		while True:
			start = ticks_ms()
			ot = ntp.datetime

			hour = ot[3]
			minute = ot[4]
			second = ot[5]

			# 24 hour time to 12
			if hour > 11:
				hour = hour - 12

			angle_minute = 6 * minute + round((second/60) * 6)
			angle_hour = 30 * hour + round((minute/60) * 30)

			if last_angle_hour != angle_hour:
				splash[1] = self.gen_hand(angle_hour, fraction = 0.6, width=self.hand)
				last_angle_hour = angle_hour

			if last_angle_min != angle_minute:
				splash[2] = self.gen_hand(angle_minute, fraction=0.9, width=self.hand)
				last_angle_min = angle_minute

			splash[4] = self.gen_digital(hour, minute, second)

			for i in range(3):
				es=ticks_ms()
				#self.draw_all_hands(cx, cy, second * 6, second, minute, hour )
				splash[3] = self.gen_hand(second * 6 + (i*2), fraction=0.8)
				display.refresh()
				
				remaining = (333 -(ticks_ms()-es)) / 1000
				#print(remaining)
				
				sleep(remaining if remaining > 0 else 0 )

				# es=ticks_ms()
				# #self.draw_all_hands(cx, cy, second * 6 + 2, second, minute, hour )
				# splash[3] = self.gen_hand(second * 6 + 2, fraction=0.8)
				# display.refresh()

				# sleep( (333-(ticks_ms()-es)) / 1000 )

				# #self.draw_all_hands(cx, cy, second * 6 + 4, second, minute, hour )
				# splash[3] = self.gen_hand(second * 6 + 4, fraction=0.8)
				# display.refresh()

				# sleep_ms(.02)
				# await asyncio.sleep_ms( 333-(ticks_ms()-es) )
			
			while second == ntp.datetime[5]:
				sleep(.05)
