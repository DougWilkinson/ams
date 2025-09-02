

from versions import versions
versions[__name__] = 5
# 5: compatible with PC version and includes async scrolling

from hass import ha_setup
clock_color = 1
# Leave above when transfering from PC version

import asyncio
from logger import info, error, debug
from localtime import offset_time
from system import config
from events import low_power

from math import sin, cos
from device import Device

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

# Generate a digit with offset
class Digits:

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

		self.in_spin = False

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
		self.rotate(force=True)

	# rotate the copy of the original shape
	def rotate(self, x=0, y=0, z=0, force=False):
		if x:
			self.x_angle += x
		if y:
			self.y_angle += y
		if z:
			self.z_angle += z
		#print(f'x: {self.x_angle} + {x}, y: {self.y_angle} + {y}, z: {self.z_angle} + {z}')
		for i in range(len(self.shape)):
			if x or force:
				self.rotated[i] = rotate_3dpoint(self.shape[i], self.x_angle, (1,0,0))
			else:
				self.rotated[i] = self.shape[i]
			if y or force:
				self.rotated[i] = rotate_3dpoint(self.rotated[i], self.y_angle, (0,1,0))
			if z or force:
				self.rotated[i] = rotate_3dpoint(self.rotated[i], self.z_angle, (0,0,1))

class Clock3D:
	def __init__(self, name, display, scale=0.44):

		self.display = display
		self.scale = scale

		self.cx = self.display.width/2
		self.cy = self.display.height/2

		# used to compare to current time
		self.last_time = [0, 0, 10, 0, 0, 10, 0, 0]
		self.buffer = []
		for i in range(8):
			self.buffer.append(Digits([self.last_time[i]], scale=self.scale, xo=i-3, yo=0 ) )
		
		self.onoff = Device(name, state="ON", dtype="switch", notifier_setup=ha_setup)

		# asyncio.create_task(self.onoff_handler())
		# asyncio.create_task(self.update_display())
		asyncio.create_task(self.onoff_handler())
		asyncio.create_task(self.update_display())

	async def onoff_handler(self):
		async for _ , ev in self.onoff.q:
			debug("onoff: {}".format(ev) )
			if 'OFF' in ev:
				self.display.display_off()
			else:
				self.display.display_on()
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
			self.display.line( int(ax), int(ay), int(bx), int(by), color)


	async def flip_digit(self, digit: Digits, new_value, speed, wait_for_event, finished_event ):
		#print("In flip_digit new value: {}".format(new_value) )
		await wait_for_event.wait()

		if digit.in_spin:
			finished_event.set()
			return
		
		if low_power.is_set():
			self.draw(digit, 0)
			digit.x_angle = 0
			digit.y_angle = 0
			digit.z_angle = 0
			digit.render(new_value)
			self.draw(digit, clock_color)
			finished_event.set()
			return
		
		digit.in_spin = True

		for angle in range(5):
			self.draw(digit, 0)
			digit.rotate(0.32, 0, 0 )
			#print("Out: {} :".format(i), self.buffer[i].y_angle)
			self.draw(digit, clock_color)
			await asyncio.sleep(speed)

		# erase old digit
		self.draw(digit, 0)

		# draw new digit while rotating
		digit.x_angle = -1
		digit.render(new_value)
		self.draw(digit, clock_color)
		#print("Addnew: {} :".format(i), self.buffer[i].y_angle)

		finished_event.set()
		await asyncio.sleep(speed)

		for angle in range(5):
			self.draw(digit, 0)
			if angle == 9: 
				digit.x_angle = 0
				digit.y_angle = 0
				digit.z_angle = 0
				digit.render(new_value)
			else:
				digit.rotate(0.2, 0, 0 )
			#print("In: {} :".format(i), self.buffer[i].y_angle)
			self.draw(digit, clock_color)
			await asyncio.sleep( speed)

		digit.in_spin = False


	async def update_display(self):
		
		try:		
			while True:

				hour = "{:02d}".format(offset_time()[3] )
				minute = "{:02d}".format(offset_time()[4] )
				second = "{:02d}".format(offset_time()[5] )

				current_time = [int(hour[0]), int(hour[1]), 10, int(minute[0]), int(minute[1]), 10, int(second[0]), int(second[1]) ]
				#print(f'current_time: {current_time} last_time: {self.last_time} ' )

				if current_time != self.last_time:

					always_do = asyncio.Event()
					always_do.set()

					asyncio.create_task(self.flip_digit(self.buffer[7], [current_time[7]], 0.001 , always_do, always_do ) )
					
					wait_for_next = asyncio.Event()

					if second[1] == '0':
						for i in range(7):
							if i == 2 or i == 5:
								self.draw(self.buffer[i], clock_color)
								continue
							# if current_time[i] != self.last_time[i]:
							finished_event = asyncio.Event()
							asyncio.create_task(self.flip_digit(self.buffer[i], [current_time[i]], 0.006 , finished_event, wait_for_next ) )
							wait_for_next = finished_event
						finished_event.set()
					self.last_time = current_time
				
				self.display.show()
				
				await asyncio.sleep(.001)
		except Exception as e:
			config.last_exception = 'clock3da.update_display: ' + e
			print("clock3da.update_display error: {}".format(e) )

