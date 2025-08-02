# events.py

import asyncio

# events used across various modules

wifi_connected = asyncio.Event()
mqtt_connected = asyncio.Event()
time_synced = asyncio.Event()
