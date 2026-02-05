# air-s3.py

from versions import versions
versions[__name__] = 10
# 10: converted to new standard (no hass_setup)

from ble import init_poll_for, init_scan_for
from air import WP6003
from govee import Govee5074
from hlkradar import HLKRadar

init_scan_for(Govee5074)
init_scan_for(HLKRadar)
init_poll_for(WP6003)

#co2 = Analog("kitchen_co2", pin=36, diff=.1, poll_seconds=60, k=159.3, units="v")
#motion = Binary(name="refrigerator_motion", pin=39)

