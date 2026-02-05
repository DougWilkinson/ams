# stove.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig (no hass_setup)
# 11: removed dht for under sink (causing spurious motion triggers?) 1/31/2026

#from dht import DHT22
#from machine import Pin
#from dhtx import DHTX
#from device import Device
from binary import Binary
from analog import Analog

# dhtx.init("stove", DHT22(Pin(13) ) )
#sink = DHTX("sink", DHT22(Pin(11) ) )

motion = Binary("stove_motion", 13 )
co2 = Analog("stove_co2", pin=9, diff=.1, poll_seconds=60, k=159.3, units="v")

