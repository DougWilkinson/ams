# analogwatch.py

from versions import versions
versions[__name__] = 10
# 10: refactored version with new Device and hass changes

from machine import SPI, Pin
from logger import info, debug, error
from gc9a01 import GC9A01
#from xglcd_font import XglcdFont
from blitclock import BlitClock


# blank = '{"nws": {"color": 63488, "text": "loading ...            ", "x": 0, "y": 291}, "source": {"color": 63488, "text": "---  ", "x": 0, "y": 15}, "temp": {"color": 38924, "text": "--.-\u0027F  ", "x": 120, "y": 15}}'
# weather = Device("weather", "", notifier_setup=ha_setup )

# weather.set_state(blank)


display_spi = SPI(1, baudrate=33_000_000, sck=14, mosi=13, miso=12)
ssd = GC9A01(display_spi, Pin(15, Pin.OUT, value=1), Pin(5, Pin.OUT, value=0), Pin(4, Pin.OUT, value=1), usd=True)

#font = XglcdFont('Lucida_Console18x29.c',18,29)

oledclock = BlitClock("test_watch",  display=ssd, color=ssd.BLUE )
