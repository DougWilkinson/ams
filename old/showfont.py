
from machine import SPI, Pin
from ili9341fb import Ili9341
from xglcd_font import XglcdFont
from framebuf import FrameBuffer, RGB565
backlight = Pin(9, Pin.OUT)
backlight.on()

spi = SPI(1, baudrate=8888888, sck=6, mosi=11, miso=10)
display = Ili9341(spi, rotation=180, cs=7, dc=5, rst=4)

def show(file,w,h):
	font = XglcdFont(file,w,h)
	color = 63488
	display.show()
	nw = w
	nh = h
	for scale in range(1,7,1):
		x = 2
		y = scale * nh + 2
		for letter in "abcABC012:-":
			# grab bytearray for letter
			letter_data, w, h = font.get_letter(letter, color, 0, False)

			# get bytearry for scaled letter and scaled width/height
			scaled_letter, nw, nh = scale_letter(letter_data, w, h, scale)
			# print("scaled to w={}, h={}".format(nw,nh) )

			# convert to buffer
			scaled_letter_buff = FrameBuffer(scaled_letter, nw, nh, RGB565 )
			
			# draw it and return position for next
			nw, nh = draw_letter_buff(x,y, scaled_letter_buff, nw, nh )
			# draw space (1 pixel)
			display.rect(x + nw, y, scale, nh, 0)
			x += nw + scale

def scale_letter(letter_data, w, h, scale_factor):

	scaled_width = w * scale_factor
	scaled_height = h * scale_factor
	scaled_data = bytearray(0)

	for row in range(scaled_height):
		for col in range(scaled_width):
			orig_row = row // scale_factor
			orig_col = col // scale_factor
			index = orig_row * w * 2 + (orig_col * 2) 
			scaled_data.append(letter_data[index])
			scaled_data.append(letter_data[index+1])

	return scaled_data, scaled_width, scaled_height

def draw_letter_buff(x, y, letter_buff, w, h):
	display.block(x, y,
				x + w - 1, y + h - 1,
				letter_buff)
	return w, h
