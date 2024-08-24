# touchmeds.py

version = (2, 0, 0)
# 208: converted to class version LedMotion
# 209: added superclass cover/limit

from machine import SPI
from core import info, latch
from ili9341 import Ili9341
from xglcd_font import XglcdFont
from oledclock import OLEDClock
from hass import ha_setup
from device import Device

blank = '{"nws": {"color": 63488, "text": "loading ...            ", "x": 0, "y": 291}, "source": {"color": 63488, "text": "---  ", "x": 0, "y": 15}, "temp": {"color": 38924, "text": "--.-\u0027F  ", "x": 120, "y": 15}}'
weather = Device("weather", "", notifier_setup=ha_setup )
weather.set_state(blank)

#			"ili9341p": { "baudrate": 8888888, "effect": "centered", "hand": 5,
#						"width": 240, "height": 320, "radius": 100, "color" : 31  },

spi = SPI(1, baudrate=8888888)
display = Ili9341(spi, rotation=180)
font = XglcdFont('fonts/Lucida_Console18x29.c',18,29)
oledclock = OLEDClock("touchmeds", oled=display, color=31, radius=100, text=weather, font=font)

async def start(hostname):
		await latch.wait()
