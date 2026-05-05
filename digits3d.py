# digits3d.py (originally from clock3dblit.py)
# only supports MONO_VLSB framebuffer

from versions import versions
versions[__name__] = 17
# 5: compatible with PC version and includes async scrolling
# 10: refactored version with new Device and hass changes
# 11: speed set to 0 where noted
# 15: complete rewrite to use blit buffers and pre-rendered segments
# 16: added on/off handling back in
# 17: added support to turn clock updates on or off to allow other functions (like scale display)
# 18: renamed and made a standalone 3d digit rendering class for displays using blit buffers


import asyncio
from logger import info, error, debug
from framebuf import FrameBuffer, MONO_VLSB

from math import sin, cos

# segment order:
# top, right top, right bottom, bottom, left bottom, left top, middle
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
	[0,0,0,0,0,0,0,1], # 10 colon
	[0,0,0,0,0,0,1], # 11 dash
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
# digits are 21 pixels wide by 32 pixels high (at scale = 1)
# to and from blit lists are 5 blit buffers each
# from_blits would be used to make the number disappear by rotating in 3d to a "dashed" line
# to_blits would be used to make the number appear by rotating from a dashed line to this number
# scale can be used to change the size of the rendering, but the resulting image may have artifacts
class Digit:

	def __init__(self, value, scale=0.5):
		
		self.scale = scale
		self.width = int(24 * scale)
		self.height = int(44 * scale)

		# Start with the from_value shape at angle = 0
		shape = generate_shape(value, scale)

		# use when transitioning from this value
		self.from_blits = []
		angle = 0

		for i in range(5):

			self.from_blits.append(render_blit(shape, self.width, self.height, angle, 1 ) )
			angle += 0.32

		angle = -1

		# use when transitioning to this value
		self.to_blits = []
		for i in range(5):		

			self.to_blits.append(render_blit(shape, self.width, self.height, angle, 1 ) )
			angle += 0.2

# Generate all digits using scale and retun a list of Digit objects
def generate_digits(scale=0.4) -> list:
	info(f"generate_digits: using scale: {scale}")

	digits = []
	for n in range(len(seven_segment_def)):
		digits.append( Digit(n, scale) )

	return digits
