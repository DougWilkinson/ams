# analogclock.py

from versions import versions
versions[__name__] = 3

from machine import SPI, Pin
from core import info, latch
from ili9341fb import Ili9341
from xglcd_font import XglcdFont
# from oledclock import OLEDClock
from blitclock import BlitClock
from hass import ha_setup
from device import Device
import asyncio

latch = asyncio.Event() 

backlight = Pin(9, Pin.OUT)
backlight.on()

blank = '{"nws": {"color": 63488, "text": "loading ...            ", "x": 0, "y": 291}, "source": {"color": 63488, "text": "---  ", "x": 0, "y": 15}, "temp": {"color": 38924, "text": "--.-\u0027F  ", "x": 120, "y": 15}}'
weather = Device("weather", "", notifier_setup=ha_setup )

weather.set_state(blank)


spi = SPI(1, baudrate=8888888, sck=6, mosi=11, miso=10)
display = Ili9341(spi, rotation=180, cs=7, dc=5, rst=4)
font = XglcdFont('Lucida_Console18x29.c',18,29)
oledclock = BlitClock("analogclock",  oled=display, color=63488, text=weather, font=font )

async def start(hostname):
		await latch.wait()
