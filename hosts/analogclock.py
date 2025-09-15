# analogclock.py

from versions import versions
versions[__name__] = 4

from machine import SPI, Pin, SoftSPI
from core import info, latch
from ili9341fb import Ili9341
from xpt2046 import Touch
from xglcd_font import XglcdFont
from blitclock import BlitClock
from hass import ha_setup
from device import Device
import asyncio

latch = asyncio.Event() 

# backlight = Pin(9, Pin.OUT)
# backlight.on()

blank = '{"nws": {"color": 63488, "text": "loading ...            ", "x": 0, "y": 291}, "source": {"color": 63488, "text": "---  ", "x": 0, "y": 15}, "temp": {"color": 38924, "text": "--.-\u0027F  ", "x": 120, "y": 15}}'
weather = Device("weather", "", notifier_setup=ha_setup )

weather.set_state(blank)

# original
touch_spi = SoftSPI(baudrate=1000000, sck=Pin(39), mosi=Pin(38), miso=Pin(40))
touch = Touch(touch_spi, cs=Pin(42), width=240, height=320)

# softspi definitely caused issues, SPI still supported
# can't use -1 for SPI id#, that denotes softSPI, now deprecated
#display_spi = SoftSPI(baudrate=8888888, sck=6, mosi=11, miso=10)
display_spi = SPI(1, baudrate=8888888, sck=6, mosi=11, miso=10)

display = Ili9341(display_spi, rotation=180, cs=7, dc=5, 
				rst=4, backlight=9)
font = XglcdFont('Lucida_Console18x29.c',18,29)
oledclock = BlitClock("analogclock",  display=display, color=63488, text=weather, font=font )

async def start(hostname):
		await latch.wait()
