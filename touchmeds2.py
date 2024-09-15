# touchmeds2.py

from versions import versions
versions[__name__] = 3

from machine import SPI, Pin
from core import info, latch, use_wifi
from ili9341fb import Ili9341
#from xglcd_font import XglcdFont
# from oledclock import OLEDClock
from oledtest import OLEDClock
# from hass import ha_setup
# from device import Device

use_wifi.clear()

backlight = Pin(39, Pin.OUT)
backlight.on()
#blank = '{"nws": {"color": 63488, "text": "loading ...            ", "x": 0, "y": 291}, "source": {"color": 63488, "text": "---  ", "x": 0, "y": 15}, "temp": {"color": 38924, "text": "--.-\u0027F  ", "x": 120, "y": 15}}'
#weather = Device("weather", "", notifier_setup=ha_setup )
#weather.set_state(blank)

#			"ili9341p": { "baudrate": 8888888, "effect": "centered", "hand": 5,
#						"width": 240, "height": 320, "radius": 100, "color" : 31  },

spi = SPI(1, baudrate=8888888, sck=36, mosi=35, miso=37)
display = Ili9341(spi, rotation=180, cs=34, dc=38, rst=40)
#font = XglcdFont('Lucida_Console18x29.c',18,29)
oledclock = OLEDClock("touchmeds", oled=display, color=28689, radius=100, text=None, font=None, )

async def start(hostname):
		await latch.wait()
