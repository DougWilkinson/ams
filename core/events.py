# events.py

from versions import versions
versions[__name__] = 11
# 10: refactored version with Device changes
# 11: added status_changed event

import asyncio

# events used across various modules

# If client wifi connected successfully
wifi_connected = asyncio.Event()

# set if wifi status is bad password or ssid not set
wifi_unconfigured = asyncio.Event()

# set if wifi status is bad password
wifi_bad_password = asyncio.Event()

# modules that use config settings should reapply configs when this is set
config_changed = asyncio.Event()
config_wifi_changed = asyncio.Event()
config_timezone_changed = asyncio.Event()
config_mqtt_changed = asyncio.Event()

# set if time has been updated by an external source in past 90 seconds
# system resets to make sure this is set again by external source
time_synced = asyncio.Event()

# set to tell modules to "do less" if possible to free up resources
low_power = asyncio.Event()

# signal that mqtt is connected and other downstream events can now run
mqtt_connected = asyncio.Event()

# set by notifier if error to to trigger upstream reconnect
mqtt_error = asyncio.Event()

# set to trigger resubscribe for notifier
subscribe_all = asyncio.Event()

# Set when new devices are added
device_added = asyncio.Event()

# Set to update esp state and attributes in mqttserver
status_changed = asyncio.Event()
