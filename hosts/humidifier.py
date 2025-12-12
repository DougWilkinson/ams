# humidifier.py

from versions import versions
versions[__name__] = 1
# 1: converted to new standard for device and hass

from hx711 import HX711
from scale import Scale

#hx = HX711(hxclock_pin=18, hxdata_pin=19, k=229, max=1000, offset=1450, samples=5)
hx = HX711(hxclock_pin=13, hxdata_pin=12, k=229, max=1000, offset=1450, samples=5)
water_level = Scale("humidifier_water", hx, diff=10)

