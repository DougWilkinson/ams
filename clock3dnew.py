# clock3dnew.py

from versions import versions
versions[__name__] = 20

# 20: pre-rendered segments but not blit buffers

clock_color = 1
# Leave above when transfering from PC version

import asyncio
from logger import info, error, debug
from localtime import offset_time
from system import config
from events import low_power
from framebuf import FrameBuffer, MONO_VLSB
import time

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

def rotate_shape(shape, angle):
	"""Rotate a 3D shape around X axis."""
	new_shape = []
	for point in shape:
		new_shape.append(rotate_3dpoint(point, angle, [1, 0, 0]))
	return new_shape

# Generate a shape (list of points) for a digit to scale
def generate_shape(digit, scale) -> list:
	shape = []

	segments = seven_segment_def[digit]
	# iterate for each segment in digit
	for segment in range(len(segments)):
		if segments[segment] == 1:
			for coords in segment_lines[segment]:
				shape.append( ( coords[0] * scale, coords[1] * scale, coords[2] * scale ) )

	return shape

# given a shape and angle return a framebuffer object
def render_blit(shape, width, height, angle, color):
	
	# rotate the shape object to be used for rendering to framebuffer
	# angle is absolute from 0
	rotated_shape = rotate_shape(shape, angle)

	# calculate origin as coordinates are from center
	origin_x = width / 2
	origin_y = height / 2

	frame_buffer = FrameBuffer(bytearray(width * height), width, height, MONO_VLSB)

	# print(f'shape: {shape}')
	# coordinates are in pairs and we do not wrap back to start
	for i in range(0, len(rotated_shape)-1, 2):
		a = rotated_shape[i]
		b = rotated_shape[(i + 1) ]
		ax, ay = (a[0] ) + (a[2] * 0.3 ) + origin_x, (a[1] ) + (a[2] * 0.3 ) + origin_y
		bx, by = (b[0] ) + (b[2] * 0.3 ) + origin_x, (b[1] ) + (b[2] * 0.3 ) + origin_y
		frame_buffer.line( int(ax), int(ay), int(bx), int(by), color)

	return frame_buffer

# Hold all angles of a digit and methods for rendering
# create a blit buffer for each angle?
# 7 segment display is 21 pixels wide by 32 pixels high (scale = 1)
# 
class Digit:

	def __init__(self, value, scale=0.5):
		
		self.scale = scale
		self.width = int(24 * scale)
		self.height = int(44 * scale)

		# Start with the from_value shape at angle = 0
		shape = generate_shape(value, scale)

		# use when transitioning from this value
		self.from_shapes = []
		angle = 0

		for i in range(5):

			self.from_shapes.append(rotate_shape(shape, angle ) )
			angle += 0.32

		angle = -1

		# use when transitioning to this value
		self.to_shapes = []
		for i in range(5):		

			self.to_shapes.append(rotate_shape(shape, angle ) )
			angle += 0.2

class Clock:
	def __init__(self, display, x=0, y=21, scale=0.4):

		self.scale = scale
		self.x = x
		self.y = y

		self.display = display
		
		# set to signal a refresh of display is needed
		self.refresh = asyncio.Event()
		self.refresh.set()

		# generate all digits
					
		self.digits = []
		for n in range(11):
			self.digits.append( Digit(n, scale) )

		# digit width and height
		self.origin_x = int(12 * scale)
		self.origin_y = int(22 * scale)

		self.last_time = [0, 0, 10, 0, 0, 10, 0, 0]
		self.current_time = [0, 0, 10, 0, 0, 10, 0, 0]

		always_event = asyncio.Event()
		always_event.set()

		# triggered when you want the cascading flip to happen (every 10 seconds?)
		self.cascade_trigger = asyncio.Event()

		self.every_second = asyncio.Event()
		self.seconds_done = asyncio.Event()

		x = -15

		for place in range(7):
			
			# each digit is placed 12 pixels apart
			# TODO: make this pull Digit.width from one of the digits

			x += 16

			info("placing digit: {} at x={}".format(place, x) )

			chain_event = asyncio.Event()

			if place == 2 or place == 5:
				info("placing colon at x={}".format(x) )
				self.render_shape(self.digits[10].from_shapes[0], x, y, 1)
				continue

			if place == 0:
				asyncio.create_task(self.maintain_digit(place, x, y, always_event, chain_event ) )
				next_event = chain_event
				continue

			if place == 6:
				asyncio.create_task(self.maintain_digit(place, x, y, next_event, self.cascade_trigger ) )
				continue

			asyncio.create_task(self.maintain_digit(place, x, y, next_event, chain_event ) )

			next_event = chain_event

		# do seconds last digit (trigger and done events are different)
		x += 16
		info("placing digit: 7 at x={}".format(x) )
		asyncio.create_task(self.maintain_digit( 7, x, y, self.seconds_done, self.every_second ) )

		asyncio.create_task(self.maintain_time() )
		asyncio.create_task(self.update_display() )
		
	def render_shape(self, shape, x, y,color):
		
		for i in range(0, len(shape)-1, 2):
			a = shape[i]
			b = shape[(i + 1) ]
			ax, ay = (a[0] ) + (a[2] * 0.3 ) + x + self.origin_x, (a[1] ) + (a[2] * 0.3 ) + y + self.origin_y
			bx, by = (b[0] ) + (b[2] * 0.3 ) + x + self.origin_x, (b[1] ) + (b[2] * 0.3 ) + y + self.origin_y
			self.display.line( int(ax), int(ay), int(bx), int(by), color)


	async def maintain_digit(self, place, x, y, next_trigger, wait_until):
		# set the digit to the current value when initialized
		info("started: maintaining digit place: {}".format(place) )
		wait_until.set()
		last = self.current_time[place]
		while True:
			# wait for last digit to trigger this one
			await wait_until.wait()
			wait_until.clear()

			# spin digit
			for shape in self.digits[last].from_shapes:
				self.render_shape(shape, x, y, 1)
				self.refresh.set()
				await asyncio.sleep(0.01)
				self.render_shape(shape, x, y, 0)
				# self.display.show()
				# time.sleep(0.01)
			next_trigger.set()

			# set the digit to the current value when initialized
			current = self.current_time[place]
			# spin digit
			for i in range(5):
				shape = self.digits[current].to_shapes[i]
				self.render_shape(shape, x, y, 1)
				self.refresh.set()
				await asyncio.sleep(0.01)
				# self.display.show()
				# time.sleep(0.01)
				
				self.render_shape(shape, x, y, 0)

			self.render_shape(self.digits[current].from_shapes[0], x, y, 1)
			self.refresh.set()			
			last = current


	async def maintain_time(self):
		info("started: maintaining time")
		last_second = -1
		while True:

			hour = "{:02d}".format(offset_time()[3] )
			minute = "{:02d}".format(offset_time()[4] )
			second = "{:02d}".format(offset_time()[5] )

			self.current_time[0] = int(hour[0])
			self.current_time[1] = int(hour[1])
			self.current_time[3] = int(minute[0])
			self.current_time[4] = int(minute[1])
			self.current_time[6] = int(second[0])
			self.current_time[7] = int(second[1])

			if last_second == second:
				await asyncio.sleep(0)
				continue

			# print("last: {} current: {}".format(last_second, second) )
			
			# kick off seconds digit to flip
			last_second = second
			self.every_second.set()

			# wait for seconds digit to start flip before starting the rest
			self.seconds_done.clear()
			await self.seconds_done.wait()

			if second[1] == "0":
				self.cascade_trigger.set()

	async def update_display(self):
		info("started: updating display")
		while True:
			await self.refresh.wait()
			self.display.show()
			self.refresh.clear()

# def demo(display, scale=1, speed=0):
# 	blits = []
# 	for d in range(10):
# 		blits.append(DigitView(d, scale=scale))
# 	last = 0
# 	current = 0
# 	while True:
# 		for blit in blits[last].blits_out:
# 			display.blit(blit, 20, 10)
# 			display.show()
# 			time.sleep(speed)

# 		for blit in blits[current].blits_in:
# 			display.blit(blit, 20, 10)
# 			display.show()
# 			time.sleep(speed)

# 		last = current
# 		current = (current + 1) % 10
# 		time.sleep(.2)
	
# class Clock3D:
# 	def __init__(self, name, display, scale=0.44):

# 		self.display = display
# 		self.scale = scale

# 		# array to hold Digit objects for each digit
# 		self.digits = []

# 		# generate Digit objects 0 - 9 (10 is colon)
# 		for digit in range(11):
# 			self.digits.append(DigitView(digit, scale=self.scale) )

# 		# used to compare to current time
# 		self.last_time = [0, 0, 10, 0, 0, 10, 0, 0]

# 		self.onoff = Device(name, state="ON", dtype="switch")

# 		# asyncio.create_task(self.onoff_handler())
# 		# asyncio.create_task(self.update_display())
# 		asyncio.create_task(self.onoff_handler())
# 		asyncio.create_task(self.update_display())

# 	async def onoff_handler(self):
# 		async for _ , ev in self.onoff.q:
# 			debug("onoff: {}".format(ev) )
# 			if 'OFF' in ev:
# 				self.display.display_off()
# 			else:
# 				self.display.display_on()

# 	# current digit, new digit values (integers) to display
# 	# speed is delay to slow flip down
# 	# offset is x offset where digit should be drawn on display
# 	# wait_for_event used to wait until previous digit flip is complete
# 	# finished_event used to signal when flip is complete (signal to next digit to start flip)
	
# 	async def flip_digit(self, current, new, speed, offset, wait_for_event, finished_event ):
# 		#print("In flip_digit new value: {}".format(new_value) )
# 		await wait_for_event.wait()
		
# 		if low_power.is_set():
# 			self.display.blit(self.digits[new].blits_out[0], offset, self.cy, 1)
# 			digit.x_angle = 0
# 			digit.y_angle = 0
# 			digit.z_angle = 0
# 			digit.render(new_value)
# 			self.draw(digit, clock_color)
# 			finished_event.set()
# 			return
		
# 		digit.in_spin = True

# 		for angle in range(5):
# 			self.draw(digit, 0)
# 			digit.rotate(0.32, 0, 0 )
# 			#print("Out: {} :".format(i), self.buffer[i].y_angle)
# 			self.draw(digit, clock_color)
# 			await asyncio.sleep(speed)

# 		# erase old digit
# 		self.draw(digit, 0)

# 		# draw new digit while rotating
# 		digit.x_angle = -1
# 		digit.render(new_value)
# 		self.draw(digit, clock_color)
# 		#print("Addnew: {} :".format(i), self.buffer[i].y_angle)

# 		finished_event.set()
# 		await asyncio.sleep(speed)

# 		for angle in range(5):
# 			self.draw(digit, 0)
# 			if angle == 9: 
# 				digit.x_angle = 0
# 				digit.y_angle = 0
# 				digit.z_angle = 0
# 				digit.render(new_value)
# 			else:
# 				digit.rotate(0.2, 0, 0 )
# 			#print("In: {} :".format(i), self.buffer[i].y_angle)
# 			self.draw(digit, clock_color)
# 			await asyncio.sleep( speed)

# 		digit.in_spin = False


# 	async def update_display(self):
		
# 		try:		
# 			while True:

# 				hour = "{:02d}".format(offset_time()[3] )
# 				minute = "{:02d}".format(offset_time()[4] )
# 				second = "{:02d}".format(offset_time()[5] )

# 				current_time = [int(hour[0]), int(hour[1]), 10, int(minute[0]), int(minute[1]), 10, int(second[0]), int(second[1]) ]
# 				#print(f'current_time: {current_time} last_time: {self.last_time} ' )

# 				x_position = self.display.width - self.digits[0].blits_out[0].width
# 				x_offset = self.digits[0].blits_out[0].width

# 				if current_time != self.last_time:

# 					always_do = asyncio.Event()
# 					always_do.set()

# 					# speed set to 0 for new rewrite
# 					# always flip the last digit (seconds)
# 					asyncio.create_task(self.flip_digit(self.last_time[7], [current_time[7]], 0 , x_offset, always_do, always_do ) )
					
# 					wait_for_next = asyncio.Event()

# 					# flip all others in sequence if seconds turns over to 0
# 					if second[1] == '0':
# 						for i in range(7):

# 							# check for colon positions
# 							if i == 2 or i == 5:
# 								# just draw the colons, do not flip them
# 								self.draw(self.buffer[i], clock_color)
# 								continue

# 							# if current_time[i] != self.last_time[i]:
# 							finished_event = asyncio.Event()
							
# 							asyncio.create_task(self.flip_digit(self.last_time[i], [current_time[i]], 0.01, x_offset , finished_event, wait_for_next ) )
							
# 							wait_for_next = finished_event
						
# 						finished_event.set()
# 					self.last_time = current_time
				
# 				self.display.show()
				
# 				# speed set to 0 for version 11
# 				await asyncio.sleep(0)
# 		except Exception as e:
# 			config.last_exception = 'clock3da.update_display: ' + e
# 			print("clock3da.update_display error: {}".format(e) )

