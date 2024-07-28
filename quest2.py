# quest2.py

version = (2,0,0)

from alog import error, latch
from machine import Pin, I2C

from ina219 import INA219
from cable import Cable
from analog import Analog
from switchmotion import SwitchMotion

# defaults = { "scl": 5,
# 	"sda": 4,
# 	"name": "current",
# 	"k": 0.0000214292,
# 	"diff": 0.05,
# 	"trip_threshold": 0.7,
# 	"trip_pin": 14,
# 	"shutoff_value": 0
# 	}

# defaults = { "pin": 0,
# 		"poll": 100,
# 		"minval": 0,
# 		"maxval": 4000,
# 		"diff": 0.1,
# 		"k": 159.3,
# 		"units": "v",
# 		"attrs": "",
# 		"threshold": 4.89642,
# 		"probe_pin": 12,
# 		"disable_pin": 14
# 		}

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
adc = Analog("cable_test", poll_seconds=0 )
relay_pin = Pin(14, Pin.OUT)

# No motion, just switch
relay_switch = SwitchMotion("quest2_relay", 14)

amps = INA219("quest2_charging_current", i2c, 
			 trip_pin_obj=relay_pin, 
			 trip_threshold_amps=0.9, 
			 diff=0.05)

cable = Cable("quest_connected", 12, adc_read=adc.adc_read, adc_poll_ms=0.05,
			  k=159.3, adc_diff=0.1 )

async def start(hostname):
	await latch.wait()

