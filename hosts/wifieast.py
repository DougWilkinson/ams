# wifieast.py

from versions import versions
versions[__name__] = 10
# 10: using webconfig (no ha_setup)

from wifiscanner import WifiScanner

scanner = WifiScanner("wifieast")
