# bed.py

from versions import versions
versions[__name__] = 10
# 10: webconfig and no hass_setup

from hx711 import HX711
from scale import Scale

# USB (side near dresser)
left_hx = hx=HX711(hxclock_pin=4, hxdata_pin=5, k=550, offset=0, samples=5)
left_bed = Scale("lbed/scale", hx, diff=30)

# main unit (near closet)
right_hx = hx=HX711(hxclock_pin=6, hxdata_pin=7, k=-1200, offset=0, samples=5)
right_bed = Scale("rbed/scale", hx, diff=30)
