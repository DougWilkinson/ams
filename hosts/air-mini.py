# air-mini.py

from versions import versions
versions[__name__] = 10
# 10: converted to new standard (no hass_setup)

from ble import init_poll_for, init_scan_for
from air import WP6003
from govee import Govee5074
from hlkradar import HLKRadar

from analog import Analog

co2 = Analog("frontroom_co2", pin=13, diff=.1, poll_seconds=60, k=159.3, units="v")

from binary import Binary

init_scan_for(Govee5074)
init_poll_for(WP6003)

init_scan_for(HLKRadar)

#co2 = Analog("kitchen_co2", pin=36, diff=.1, poll_seconds=60, k=159.3, units="v")
motion = Binary(name="frontroom_motion", pin=8, invert=False)
