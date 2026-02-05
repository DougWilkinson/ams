# touchmeds.py

from versions import versions
versions[__name__] = 11
# 10: using webconfig and no ha_setup
# 11: changed clock sizes and moved digital clock to bottom

from machine import SPI, Pin
from logger import info, error

from ili9341fb import Ili9341
from xglcd_font import XglcdFont
from blitclock import BlitClock
from device import Device

blank = '{"nws": {"color": 63488, "text": "loading ...            ", "x": 0, "y": 291}, "source": {"color": 63488, "text": "---  ", "x": 0, "y": 15}, "temp": {"color": 38924, "text": "--.-\u0027F  ", "x": 120, "y": 15}}'
weather = Device("weather", blank, publish=False )

# weather.set_state(blank)

display_spi = SPI(1, baudrate=8888888, sck=6, mosi=11, miso=10)

display = Ili9341(display_spi, rotation=180, cs=7, dc=5, 
				rst=4, backlight=9)

font = XglcdFont('Lucida_Console18x29.c',18,29)

oledclock = BlitClock("touchmeds",  display=display, color=63488, text=weather, font=font, radius_factor=0.66, cy=145, dcy=255 )
