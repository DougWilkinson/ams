# humidifier.py

from versions import versions
versions[__name__] = 2
# 1: converted to new standard for device and hass
# 2: converted to use new k and offset to calculate hx value

from hx711 import HX711
from scale import Scale

#hx = HX711(hxclock_pin=18, hxdata_pin=19, k=229, max=1000, offset=1450, samples=5)

# before new HX method for k and offset
hx = HX711(hxclock_pin=13, hxdata_pin=12, k=229, max=1000, offset=1450, samples=5)

# using new method (my - offset)/k 
hx = HX711(hxclock_pin=13, hxdata_pin=12, k=160, min=0, max=1000, offset=-328000, samples=5, rate_ms=300)
water_level = Scale("humidifier_water", hx, diff=10)

