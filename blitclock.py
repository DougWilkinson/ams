# blitclock.py

from versions import versions
versions[__name__] = 3
# 200: async version with oled type in params

from time import sleep_ms, ticks_ms
from machine import RTC
from framebuf import FrameBuffer, RGB565
import array
import math
import json
import uasyncio as asyncio
from core import debug, offset_time
from random import randint

class BlitClock:
	
	def __init__(self, name, oled, color=31, width=None, height=None, radius_factor=0.84, text=None, font=None, hand=5, effect="centered" ):
		self.oled = oled
		self.width = width if width else self.oled.width
		self.height = height if height else self.oled.height
		# start with center of oled
		self.cx = self.width >> 1
		self.cy = self.height >> 1
		self.clock_radius = int(self.width * radius_factor / 2)
		self.text = text
		self.font = font
		self.hand = hand
		self.color = color
		self.effect = effect
		# define buffers for face and each hand
		self.face_fb = FrameBuffer(bytearray(self.width * self.height * 2), self.width, self.height, RGB565 )
		self.s_hand_fb = FrameBuffer(bytearray(self.width * self.height * 2), self.width, self.height, RGB565 )
		self.m_hand_fb = FrameBuffer(bytearray(self.width * self.height * 2), self.width, self.height, RGB565 )
		self.h_hand_fb = FrameBuffer(bytearray(self.width * self.height * 2), self.width, self.height, RGB565 )
		self.seconds_color = 63488
		asyncio.create_task(self.clock_handler())
		asyncio.create_task(self.text_handler())

	async def text_handler(self):
		async for _, ev in self.text.q:
			text = json.loads(ev)
			self.draw_face(self.color)
			for name, content in text.items():
				self.draw_text(self.face_fb, content['x'], content['y'], content['text'], content['color'])

	def getxy(self, angle, radius):
		x = round(radius * math.sin(math.radians(angle)))
		y = round(radius * math.cos(math.radians(angle)))
		return array.array('h',[x,-y])

	def update_hand(self, hand_buf, angle, fraction=1.0, width=0, color=0):
		hand_buf.fill(0)

		start = ticks_ms()
		pbase = self.getxy(angle+90, width)
		nbase = self.getxy(angle-90, width)
		longside = self.getxy(angle, self.clock_radius*fraction)
		shortside = self.getxy(angle+180, self.clock_radius * 0.2)
		# print("calc: ", ticks_ms() - start)
		start = ticks_ms()
		# Draw long side (outline)
		hand_buf.poly(self.cx, self.cy, array.array('h',pbase + nbase + longside), color, False)
		# print("long: ", ticks_ms() - start)
		start = ticks_ms()

		# Draw short side (filled in)
		hand_buf.poly(self.cx, self.cy, array.array('h',pbase + nbase + shortside), color, True)
		# print("short: ", ticks_ms() - start)

	def draw_face(self, color=0):
		self.face_fb.fill(0)
		# self.oled.draw_text(239-(len(self.outside_temp.value )*18), 0, str(self.outside_temp.value), self.lucida, 63488)
		# self.oled.draw_text(0, 291, self.weather.value, self.lucida, 63488)
		#self.draw_text()
		for i in range(12):
			self.face_fb.ellipse(self.cx + round(self.clock_radius * math.sin(math.radians(i*30))),
		    				self.cy + round(self.clock_radius * math.cos(math.radians(i*30)) ),
							self.hand-1, self.hand-1, color, color)

	# def update_hands(self, cx, cy, second_angle, second, minute, hour ):
	# 		angle_hour = 30 * hour + round((minute/60) * 30)
	# 		angle_minute = 6 * minute + round((second/60) * 6)
	# 		self.update_hand(self.h_hand, angle_hour, cx, cy, fraction = 0.6, width=self.hand, color=self.color)
	# 		self.update_hand(self.m_hand, angle_minute, cx, cy, fraction=0.9, width=self.hand, color=self.color)
	# 		self.update_hand(self.s_hand, second_angle, cx, cy, fraction=0.8, color=self.color)
	# 		self.oled.show()


	async def clock_handler(self):
		last_minute = -1
		last_hour = -1
		last_cx = -1
		last_cy = -1
		while True:
			full = ticks_ms()
			ot = offset_time()
			hour = ot[3]
			minute = ot[4]
			second = ot[5]

			# 24 hour time to 12
			if hour > 11:
				hour = hour - 12

			if last_cx != self.cx or last_cy != self.cy:
				self.draw_face(self.color)
				last_cx = self.cx
				last_cy = self.cy

			angle_hour = 30 * hour + round((minute/60) * 30)
			if angle_hour != last_hour:
				self.update_hand(self.h_hand_fb, angle_hour, fraction = 0.6, width=self.hand, color=self.color)
				last_hour = angle_hour

			angle_minute = 6 * minute + round((second/60) * 6)
			if angle_minute != last_minute:
				self.update_hand(self.m_hand_fb, angle_minute, fraction=0.9, width=self.hand, color=self.color)
				last_minute = angle_minute

			for i in range(3):
				es=ticks_ms()
				angle_second = second * 6 + ( i * 2)
				self.update_hand(self.s_hand_fb, angle_second, fraction=0.8, color=self.color)
				self.draw_text(self.s_hand_fb, 60, 190, "{}:{:0>2}:{:0>2}".format(hour,minute,second), 63)
				self.oled.blit(self.face_fb, 0, 0)
				self.oled.blit(self.h_hand_fb, 0, 0, 0)
				self.oled.blit(self.m_hand_fb, 0, 0, 0)
				self.oled.blit(self.s_hand_fb, 0, 0, 0)
				self.oled.show()

				#print(ticks_ms() - es)
				remaining = 320 - ( ticks_ms()-es )

				await asyncio.sleep_ms(remaining if remaining > 0 else 0)
			
			# print(ticks_ms() - full)
			while second == offset_time()[5]:
				sleep_ms(1)

	def draw_letter(self, frame_buffer, x, y, letter, color, background=0,
					landscape=False):
		"""Draw a letter.
			x (int): Starting X position.
			y (int): Starting Y position.
			letter (string): Letter to draw.
			font (XglcdFont object): Font.
			color (int): RGB565 color value.
			background (int): RGB565 background color (default: black).
			landscape (bool): Orientation (default: False = portrait)
		"""
		b_letter, w, h = self.font.get_letter(letter, color, background, landscape)
		# Check for errors (Font could be missing specified letter)
		if w == 0:
			return w, h

		buf = FrameBuffer(b_letter, w, h, RGB565)
		if landscape:
			y -= w
			frame_buffer.blit(buf, x, y, 0)
		else:
			frame_buffer.blit(buf, x, y, 0)

		return w, h

	def draw_text(self, frame_buffer, x, y, text, color, background=0,
				  landscape=False, spacing=1):
		"""Draw text.
			x (int): Starting X position.
			y (int): Starting Y position.
			text (string): Text to draw.
			font (XglcdFont object): Font.
			color (int): RGB565 color value.
			background (int): RGB565 background color (default: black).
			landscape (bool): Orientation (default: False = portrait)
			spacing (int): Pixels between letters (default: 1)
		"""
		for letter in text:
			# Get letter array and letter dimensions
			w, h = self.draw_letter(frame_buffer, x, y, letter, color, background,
									landscape)
			if landscape:
				# Fill in spacing
				if spacing:
					frame_buffer.rect(x, y - w - spacing, h, spacing, background)
				# Position y for next letter
				y -= (w + spacing)
			else:
				# Fill in spacing
				if spacing:
					frame_buffer.rect(x + w, y, spacing, h, background)
				# Position x for next letter
				x += (w + spacing)

				# # Fill in spacing
				# if spacing:
				#     self.fill_vrect(x + w, y, spacing, h, background)
				# # Position x for next letter
				# x += w + spacing
