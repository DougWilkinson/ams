# ili9341.py
# LCD/Touch module.

from versions import versions
versions[__name__] = 3

from time import sleep
from math import cos, sin, pi, radians
from framebuf import FrameBuffer, RGB565  # type: ignore
import ustruct  # type: ignore
from machine import Pin

def color565(r, g, b):
	# Return RGB565 color value.
	return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

# class ILI9341Buffer_SPI(FrameBuffer):
# 	def __init__(self, spi, width=240, height=136, rotation=0):
# 		# Display width=240, height=320
# 		self.display = Display(spi, rotation=rotation)
# 		self.x_zero = int(self.display.width/2)
# 		self.y_zero = int(self.display.height/2)
# 		# buffer width=240, height=136
# 		self.buff_width = width
# 		self.buff_height = height
# 		self.buffer = bytearray(width * height * 2)
# 		super().__init__(self.buffer, width, height, RGB565)

# 	def show(self):
# 		self.display.block(self.x_zero, self.y_zero, self.x_zero+self.buff_width-1, self.y_zero+self.buff_height-1, self.buffer)


class Ili9341(FrameBuffer):
	"""Serial interface for 16-bit color (5-6-5 RGB) IL9341 display.
	All coordinates are zero based.
	"""
	NOP = const(0x00)  # No-op
	SWRESET = const(0x01)  # Software reset
	RDDID = const(0x04)  # Read display ID info
	RDDST = const(0x09)  # Read display status
	SLPIN = const(0x10)  # Enter sleep mode
	SLPOUT = const(0x11)  # Exit sleep mode
	PTLON = const(0x12)  # Partial mode on
	NORON = const(0x13)  # Normal display mode on
	RDMODE = const(0x0A)  # Read display power mode
	RDMADCTL = const(0x0B)  # Read display MADCTL
	RDPIXFMT = const(0x0C)  # Read display pixel format
	RDIMGFMT = const(0x0D)  # Read display image format
	RDSELFDIAG = const(0x0F)  # Read display self-diagnostic
	INVOFF = const(0x20)  # Display inversion off
	INVON = const(0x21)  # Display inversion on
	GAMMASET = const(0x26)  # Gamma set
	DISPLAY_OFF = const(0x28)  # Display off
	DISPLAY_ON = const(0x29)  # Display on
	SET_COLUMN = const(0x2A)  # Column address set
	SET_PAGE = const(0x2B)  # Page address set
	WRITE_RAM = const(0x2C)  # Memory write
	READ_RAM = const(0x2E)  # Memory read
	PTLAR = const(0x30)  # Partial area
	VSCRDEF = const(0x33)  # Vertical scrolling definition
	MADCTL = const(0x36)  # Memory access control
	VSCRSADD = const(0x37)  # Vertical scrolling start address
	PIXFMT = const(0x3A)  # COLMOD: Pixel format set
	WRITE_DISPLAY_BRIGHTNESS = const(0x51)  # Brightness hardware dependent!
	READ_DISPLAY_BRIGHTNESS = const(0x52)
	WRITE_CTRL_DISPLAY = const(0x53)
	READ_CTRL_DISPLAY = const(0x54)
	WRITE_CABC = const(0x55)  # Write Content Adaptive Brightness Control
	READ_CABC = const(0x56)  # Read Content Adaptive Brightness Control
	WRITE_CABC_MINIMUM = const(0x5E)  # Write CABC Minimum Brightness
	READ_CABC_MINIMUM = const(0x5F)  # Read CABC Minimum Brightness
	FRMCTR1 = const(0xB1)  # Frame rate control (In normal mode/full colors)
	FRMCTR2 = const(0xB2)  # Frame rate control (In idle mode/8 colors)
	FRMCTR3 = const(0xB3)  # Frame rate control (In partial mode/full colors)
	INVCTR = const(0xB4)  # Display inversion control
	DFUNCTR = const(0xB6)  # Display function control
	PWCTR1 = const(0xC0)  # Power control 1
	PWCTR2 = const(0xC1)  # Power control 2
	PWCTRA = const(0xCB)  # Power control A
	PWCTRB = const(0xCF)  # Power control B
	VMCTR1 = const(0xC5)  # VCOM control 1
	VMCTR2 = const(0xC7)  # VCOM control 2
	RDID1 = const(0xDA)  # Read ID 1
	RDID2 = const(0xDB)  # Read ID 2
	RDID3 = const(0xDC)  # Read ID 3
	RDID4 = const(0xDD)  # Read ID 4
	GMCTRP1 = const(0xE0)  # Positive gamma correction
	GMCTRN1 = const(0xE1)  # Negative gamma correction
	DTCA = const(0xE8)  # Driver timing control A
	DTCB = const(0xEA)  # Driver timing control B
	POSC = const(0xED)  # Power on sequence control
	ENABLE3G = const(0xF2)  # Enable 3 gamma control
	PUMPRC = const(0xF7)  # Pump ratio control

	ROTATE = {
		0: 0x88,
		90: 0xE8,
		180: 0x48,
		270: 0x28
	}

	def __init__(self, spi, cs=16, dc=4, rst=17,
				 width=240, height=320, rotation=0):
		"""Initialize OLED.
			spi (Class Spi):  SPI interface for OLED
			cs (Class Pin):  Chip select pin
			dc (Class Pin):  Data/Command pin
			rst (Class Pin):  Reset pin
			width (Optional int): Screen width (default 240)
			height (Optional int): Screen height (default 320)
			rotation (Optional int): Rotation must be 0 default, 90. 180 or 270
		"""
		self.spi = spi
		self.cs = Pin(cs)
		self.dc = Pin(dc)
		self.rst = Pin(rst)
		self.width = width
		self.height = height
		self.rotation = self.ROTATE[rotation]

		# Initialize GPIO pins and set implementation specific methods
		self.cs.init(self.cs.OUT, value=1)
		self.dc.init(self.dc.OUT, value=0)
		self.rst.init(self.rst.OUT, value=1)
		self.reset = self.reset_mpy
		self.write_cmd = self.write_cmd_mpy
		self.write_data = self.write_data_mpy
		self.reset()
		# Send initialization commands
		self.write_cmd(self.SWRESET)  # Software reset
		sleep(.1)
		self.write_cmd(self.PWCTRB, 0x00, 0xC1, 0x30)  # Pwr ctrl B
		self.write_cmd(self.POSC, 0x64, 0x03, 0x12, 0x81)  # Pwr on seq. ctrl
		self.write_cmd(self.DTCA, 0x85, 0x00, 0x78)  # Driver timing ctrl A
		self.write_cmd(self.PWCTRA, 0x39, 0x2C, 0x00, 0x34, 0x02)  # Pwr ctrl A
		self.write_cmd(self.PUMPRC, 0x20)  # Pump ratio control
		self.write_cmd(self.DTCB, 0x00, 0x00)  # Driver timing ctrl B
		self.write_cmd(self.PWCTR1, 0x23)  # Pwr ctrl 1
		self.write_cmd(self.PWCTR2, 0x10)  # Pwr ctrl 2
		self.write_cmd(self.VMCTR1, 0x3E, 0x28)  # VCOM ctrl 1
		self.write_cmd(self.VMCTR2, 0x86)  # VCOM ctrl 2
		self.write_cmd(self.MADCTL, self.rotation)  # Memory access ctrl
		self.write_cmd(self.VSCRSADD, 0x00)  # Vertical scrolling start address
		self.write_cmd(self.PIXFMT, 0x55)  # COLMOD: Pixel format
		self.write_cmd(self.FRMCTR1, 0x00, 0x18)  # Frame rate ctrl
		self.write_cmd(self.DFUNCTR, 0x08, 0x82, 0x27)
		self.write_cmd(self.ENABLE3G, 0x00)  # Enable 3 gamma ctrl
		self.write_cmd(self.GAMMASET, 0x01)  # Gamma curve selected
		self.write_cmd(self.GMCTRP1, 0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E,
					   0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)
		self.write_cmd(self.GMCTRN1, 0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31,
					   0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)
		self.write_cmd(self.SLPOUT)  # Exit sleep
		sleep(.1)
		self.write_cmd(self.DISPLAY_ON)  # Display on
		sleep(.1)
		self.buffer = bytearray(width * height * 2)
		super().__init__(self.buffer, width, height, RGB565)

		self.clear()

	def block(self, x0, y0, x1, y1, data):
		"""Write a block of data to display.
			x0 (int):  Starting X position.
			y0 (int):  Starting Y position.
			x1 (int):  Ending X position.
			y1 (int):  Ending Y position.
			data (bytes): Data buffer to write.
		"""
		self.write_cmd(self.SET_COLUMN, *ustruct.pack(">HH", x0, x1))
		self.write_cmd(self.SET_PAGE, *ustruct.pack(">HH", y0, y1))

		self.write_cmd(self.WRITE_RAM)
		self.write_data(data)

	def cleanup(self):
		"""Clean up resources."""
		self.clear()
		self.display_off()
		self.spi.deinit()
		print('display off')	

	def show(self):
		self.block(0, 0, self.width-1, self.height-1, self.buffer)
						
	def clear(self, color=0, hlines=8):
		self.fill(0)

	def draw_line(self, sx,sy, ex,ey,c):
		self.line(sx,sy,ex,ey,c)

	def display_off(self):
		"""Turn display off."""
		self.write_cmd(self.DISPLAY_OFF)

	def display_on(self):
		"""Turn display on."""
		self.write_cmd(self.DISPLAY_ON)


	def draw_letter(self, x, y, letter, font, color, background=0,
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
		buf, w, h = font.get_letter(letter, color, background, landscape)
		# Check for errors (Font could be missing specified letter)
		if w == 0:
			return w, h

		if landscape:
			y -= w
			if self.is_off_grid(x, y, x + h - 1, y + w - 1):
				return 0, 0
			self.block(x, y,
					   x + h - 1, y + w - 1,
					   buf)
		else:
			if self.is_off_grid(x, y, x + w - 1, y + h - 1):
				return 0, 0
			self.block(x, y,
					   x + w - 1, y + h - 1,
					   buf)
		return w, h

	def draw_text(self, x, y, text, font, color,  background=0,
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
			w, h = self.draw_letter(x, y, letter, font, color, background,
									landscape)
			# Stop on error
			if w == 0 or h == 0:
				return

			if landscape:
				# Fill in spacing
				if spacing:
					self.rect(x, y - w - spacing, h, spacing, background)
				# Position y for next letter
				y -= (w + spacing)
			else:
				# Fill in spacing
				if spacing:
					self.rect(x + w, y, spacing, h, background)
				# Position x for next letter
				x += (w + spacing)

				# # Fill in spacing
				# if spacing:
				#     self.fill_vrect(x + w, y, spacing, h, background)
				# # Position x for next letter
				# x += w + spacing

	def draw_text8x8(self, x, y, text, color,  background=0,
					 rotate=0):
		"""Draw text using built-in MicroPython 8x8 bit font.
			x (int): Starting X position.
			y (int): Starting Y position.
			text (string): Text to draw.
			color (int): RGB565 color value.
			background (int): RGB565 background color (default: black).
			rotate(int): 0, 90, 180, 270
		"""
		w = len(text) * 8
		h = 8
		if self.is_off_grid(x, y, x + 7, y + 7):
			return
		# Rearrange color
		r = (color & 0xF800) >> 8
		g = (color & 0x07E0) >> 3
		b = (color & 0x1F) << 3
		buf = bytearray(w * 16)
		fbuf = FrameBuffer(buf, w, h, RGB565)
		if background != 0:
			bg_r = (background & 0xF800) >> 8
			bg_g = (background & 0x07E0) >> 3
			bg_b = (background & 0x1F) << 3
			fbuf.fill(color565(bg_b, bg_r, bg_g))
		fbuf.text(text, 0, 0, color565(b, r, g))
		if rotate == 0:
			self.block(x, y, x + w - 1, y + (h - 1), buf)
		elif rotate == 90:
			buf2 = bytearray(w * 16)
			fbuf2 = FrameBuffer(buf2, h, w, RGB565)
			for y1 in range(h):
				for x1 in range(w):
					fbuf2.pixel(y1, x1,
								fbuf.pixel(x1, (h - 1) - y1))
			self.block(x, y, x + (h - 1), y + w - 1, buf2)
		elif rotate == 180:
			buf2 = bytearray(w * 16)
			fbuf2 = FrameBuffer(buf2, w, h, RGB565)
			for y1 in range(h):
				for x1 in range(w):
					fbuf2.pixel(x1, y1,
								fbuf.pixel((w - 1) - x1, (h - 1) - y1))
			self.block(x, y, x + w - 1, y + (h - 1), buf2)
		elif rotate == 270:
			buf2 = bytearray(w * 16)
			fbuf2 = FrameBuffer(buf2, h, w, RGB565)
			for y1 in range(h):
				for x1 in range(w):
					fbuf2.pixel(y1, x1,
								fbuf.pixel((w - 1) - x1, y1))
			self.block(x, y, x + (h - 1), y + w - 1, buf2)

	def is_off_grid(self, xmin, ymin, xmax, ymax):
		if xmin < 0:
			return True
		if ymin < 0:
			return True
		if xmax >= self.width:
			return True
		if ymax >= self.height:
			return True
		return False

	def load_sprite(self, path, w, h):
		"""Load sprite image.

		Args:
			path (string): Image file path.
			w (int): Width of image.
			h (int): Height of image.
		Notes:
			w x h cannot exceed 2048
		"""
		buf_size = w * h * 2
		with open(path, "rb") as f:
			return f.read(buf_size)

	def reset_mpy(self):
		self.rst(0)
		sleep(.05)
		self.rst(1)
		sleep(.05)

	def scroll(self, y):
		self.write_cmd(self.VSCRSADD, y >> 8, y & 0xFF)

	def set_scroll(self, top, bottom):
		"""Set the height of the top and bottom scroll margins.
		top (int): Height of top scroll margin
		bottom (int): Height of bottom scroll margin
		"""
		if top + bottom <= self.height:
			middle = self.height - (top + bottom)
			self.write_cmd(self.VSCRDEF,
						   top >> 8,
						   top & 0xFF,
						   middle >> 8,
						   middle & 0xFF,
						   bottom >> 8,
						   bottom & 0xFF)

	def sleep(self, enable=True):
		"""Enters or exits sleep mode.
			enable (bool): True (default)=Enter sleep mode, False=Exit sleep
		"""
		if enable:
			self.write_cmd(self.SLPIN)
		else:
			self.write_cmd(self.SLPOUT)


	def write_cmd_mpy(self, command, *args):
		"""Write command to OLED (MicroPython).
			command (byte): ILI9341 command code.
			*args (optional bytes): Data to transmit.
		"""
		self.dc(0)
		self.cs(0)
		self.spi.write(bytearray([command]))
		self.cs(1)
		# Handle any passed data
		if len(args) > 0:
			self.write_data(bytearray(args))

	def write_data_mpy(self, data):
		"""Write data to OLED (MicroPython).

		Args:
			data (bytes): Data to transmit.
		"""
		self.dc(1)
		self.cs(0)
		self.spi.write(data)
		self.cs(1)
