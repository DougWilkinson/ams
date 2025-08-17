# events.py

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

mqtt_connected = asyncio.Event()

time_synced = asyncio.Event()

low_power = asyncio.Event()