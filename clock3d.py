from math import sin, cos
from random import randrange
import time
from sh1106 import SH1106_I2C
from machine import Pin, SoftI2C

ORIGINX = 0
ORIGINY = 0


# starting with segment top left to bottom right
seven_segment_def = [
	[1,1,1,1,1,1,0], # 0
	[0,1,1,0,0,0,0], # 1
	[1,1,0,1,1,0,1], # 2
	[1,1,1,1,0,0,1], # 3
	[0,1,1,0,0,1,1], # 4
	[1,0,1,1,0,1,1], # 5
	[1,0,1,1,1,1,1], # 6
	[1,1,1,0,0,0,0], # 7
	[1,1,1,1,1,1,1], # 8
	[1,1,1,1,0,1,1], # 9
	[0,0,0,0,0,0,0,1], # colon
]

segment_lines = [
	# top segment
	[ (-6, -20,0), (6,-20,0), (-6, -19,0), (6,-19,0) ], # top segment
	# top right segment
	[ (10, -16,0), (10,-4,0), (11, -16,0), (11,-4,0)], # top right segment
	# bottom right segment
	[ (10, 4,0), (10, 16, 0), (11, 4,0), (11, 16, 0)], # bottom right segment
	# bottom segment
	[ (6, 20,0), (-6, 20,0), (6, 21,0), (-6, 21,0)], # bottom segment
	# bottom left segment
	[ (-10, 16, 0), (-10,4,0), (-9, 16, 0), (-9,4,0)], # bottom left segment
	# top left segment
	[ (-10, -4, 0), (-10,-16,0), (-9, -4, 0), (-9,-16,0)], # top left segment
	# middle segment
	[ (-6, 0,0), (6,0,0), (-6, 1,0), (6,1,0)], # middle segment
	# colon
	[ (0, -12,0), (0,-8,0), (1, -12,0), (1,-8,0),
  	 (0, 8,0), (0,12,0), (1, 8,0), (1,12,0)]
]


# Generate a digit with offset
class Digits:

	def rotate_3dpoint(p, angle, axis):
		"""Rotate a 3D point around given axis."""
		ret = [0, 0, 0]
		cosang = cos(angle)
		sinang = sin(angle)
		ret[0] += (cosang+(1-cosang)*axis[0]*axis[0])*p[0]
		ret[0] += ((1-cosang)*axis[0]*axis[1]-axis[2]*sinang)*p[1]
		ret[0] += ((1-cosang)*axis[0]*axis[2]+axis[1]*sinang)*p[2]
		ret[1] += ((1-cosang)*axis[0]*axis[1]+axis[2]*sinang)*p[0]
		ret[1] += (cosang+(1-cosang)*axis[1]*axis[1])*p[1]
		ret[1] += ((1-cosang)*axis[1]*axis[2]-axis[0]*sinang)*p[2]
		ret[2] += ((1-cosang)*axis[0]*axis[2]-axis[1]*sinang)*p[0]
		ret[2] += ((1-cosang)*axis[1]*axis[2]+axis[0]*sinang)*p[1]
		ret[2] += (cosang+(1-cosang)*axis[2]*axis[2])*p[2]
		return ret

	def __init__(self, digits: list, scale=0.3, xo=0, yo=0):
		
		self.digit_width = 35 * scale

		# what you add to the origin
		self.origin_x = int(self.digit_width * xo )
		self.origin_y = int(self.digit_width * yo )

		self.scale = scale

		# create shape of coordinates
		self.offset = - (self.digit_width * len(digits) / 2)

		self.x_angle = 0
		self.y_angle = 0
		self.z_angle = 0

		self.render(digits)


	def render(self, digits: list):
		self.shape = []
		offset_multiplier = 0
		offset = self.offset

		for d in digits:
			offset += self.digit_width * offset_multiplier
			segments = seven_segment_def[d]
			# iterate for each segment in digit
			for segment in range(len(segments)):
				if segments[segment] == 1:
					for coords in segment_lines[segment]:
						self.shape.append( ( coords[0] + offset, coords[1], coords[2] ) )
			offset_multiplier += 1
		self.rotated = self.shape.copy()
		self.rotate()

	# rotate the copy of the original shape
	def rotate(self, x=0, y=0, z=0):
		if x:
			self.x_angle += x
		if y:
			self.y_angle += y
		if z:
			self.z_angle += z
		#print(f'x: {self.x_angle}, y: {self.y_angle}, z: {self.z_angle}')
		for i in range(len(self.shape)):
			if x:
				self.rotated[i] = Digits.rotate_3dpoint(self.shape[i], self.x_angle, (1,0,0))
			if y:
				self.rotated[i] = Digits.rotate_3dpoint(self.rotated[i], self.y_angle, (0,1,0))
			if z:
				self.rotated[i] = Digits.rotate_3dpoint(self.rotated[i], self.z_angle, (0,0,1))


class Clock3D:
	def __init__(self, scale):
		#pygame.init()
		# self.screen = pygame.display.set_mode((640,400),
		# 							 HWSURFACE|DOUBLEBUF)
		sh1106_i2c = SoftI2C(scl=Pin(1),sda=Pin(2))

		self.screen = SH1106_I2C(128, 64, sh1106_i2c )


		self.scale = scale

		self.cx = self.screen.width/2
		self.cy = self.screen.height/2

		# used to compare to current time
		self.last_time = [-1, -1, -1, -1, -1, -1, -1, -1]
		self.display = []
		for i in range(8):
			self.display.append(Digits([i], scale=self.scale, xo=i-3, yo=0 ) )
		
		# self.mh = Digits([0], scale=self.scale, xo=-3, yo=0 )
		# self.lh = Digits([0], scale=self.scale, xo=-2, yo=0 )
		# self.hmc = Digits([10], scale=self.scale, xo=-1, yo=0 )
		# self.mm = Digits([0], scale=self.scale, xo=0, yo=0 )
		# self.lm = Digits([0], scale=self.scale, xo=1, yo=0 )
		# self.msc = Digits([10], scale=self.scale, xo=2, yo=0 )
		# self.ms = Digits([0], scale=self.scale, xo=3, yo=0 )
		# self.ls = Digits([0], scale=self.scale, xo=4, yo=0 )
	

	def draw(self, digit: Digits, color):
		"""
		Draw the shape on a 2D surface using Pygame.

		:param surface: The Pygame surface to draw on.
		:param color: The color of the shape.
		"""
		shape = digit.rotated
		scale = digit.scale
		origin_x = self.cx + digit.origin_x
		origin_y = self.cy + digit.origin_y

		# print(f'shape: {shape}')
		for i in range(0, len(shape)-1, 2):
			a = shape[i]
			#b = self.shape[(i + 1) % len(self.shape)]  # wrap around to the first point for the last line
			b = shape[(i + 1) ]  # do not wrap
			ax, ay = (a[0] * scale) + (a[2] * 0.3 * scale) + origin_x, (a[1] * scale) + (a[2] * 0.3 * scale) + origin_y
			bx, by = (b[0] * scale) + (b[2] * 0.3 * scale) + origin_x, (b[1] * scale) + (b[2] * 0.3 * scale) + origin_y
			self.screen.line( int(ax), int(ay), int(bx), int(by), color)

def main(scale=.44):

	clock = Clock3D(scale=scale)

	while True:
		
		hour = "{:02d}".format(time.localtime()[3] )
		minute = "{:02d}".format(time.localtime()[4] )
		second = "{:02d}".format(time.localtime()[5] )

		current_time = [int(hour[0]), int(hour[1]), 10, int(minute[0]), int(minute[1]), 10, int(second[0]), int(second[1]) ]
		#print(f'current_time: {current_time} last_time: {clock.last_time} ' )

		if current_time != clock.last_time:

				
				
			for angle in range(5):
				for i in range(8):
					if current_time[i] != clock.last_time[i]:
					
						clock.draw(clock.display[i], 0)
						clock.display[i].rotate(0.38, 0, 0 )
						# print("B:", clock.display[i].x_angle)
						clock.draw(clock.display[i], 1)
				clock.screen.show()
				#time.sleep(.05)

			# erase old digit
			for i in range(8):
				if current_time[i] != clock.last_time[i]:
					clock.draw(clock.display[i], 0)

			# draw new digit while rotating
			for i in range(8):
				if current_time[i] != clock.last_time[i]:
					clock.display[i].x_angle = 4.9
					clock.display[i].render([current_time[i]])
					clock.draw(clock.display[i], 1) 

			for angle in range(6):
				for i in range(8):
					if current_time[i] != clock.last_time[i]:

						clock.draw(clock.display[i], 0)
						if angle == 5: 
							clock.display[i].x_angle = 0
							clock.display[i].rotated = clock.display[i].shape
						else:
							clock.display[i].rotate(0.36, 0, 0 )
							# print("A:", clock.display[i].x_angle)
						clock.draw(clock.display[i], 1)
				clock.screen.show()
				#time.sleep(.05)

			clock.last_time = current_time
		
			clock.screen.show()
			#time.sleep(.2)

			#print(count)
			# clock.update_time()
			# event = pygame.event.poll()
			# if event.type == QUIT or (event.type == KEYDOWN and
			# 						event.key == K_ESCAPE):
			# 	break

			# clock.hour.render([int(hour[0]), int(hour[1])])
			# clock.minute.render([int(minute[0]), int(minute[1])])
			# clock.second.render([int(second[0]), int(second[1])])

			# #clock.hour.rotate(0.1, 0, 0 )
			# #clock.minute.rotate(0.1, 0, 0 )
			# clock.second.rotate(0.1, 0, 0 )

			# # if count == 30:
			# # 	zr=randrange(1,10)/100

			# # if count == 60:
			# 	xr=randrange(1,10)/100
			# 	count = 0
			# self.rotate_object( .01, (0,0,1))
			# self.rotate_object( .01, (1,0,0))
			# count += 1

