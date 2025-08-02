# wifi.py

from versions import versions
versions[__name__] = 1

from network import WLAN, STA_IF
from time import sleep, sleep_ms, ticks_ms
from settings import config, info, error, debug, start, reboot
from blinkled import wifi_status, on_led, off_led
from events import wifi_connected

import asyncio


wlan = WLAN(STA_IF)
wlan.active(True)

ticks_since_active = ticks_ms()

async def wifi():
	global wlan
	global config
	global wifi_connected

	# sleep at least 500 ms since last active was set True
	remaining = 500 - (ticks_ms() - ticks_since_active)
	if remaining > 0:
		sleep_ms(remaining)

	start("wifi")
	essid = wlan.config('essid')
	retries = 0

	wlan.config(dhcp_hostname=config.hostname)

	wlan.disconnect()

	wlan.connect(config.wifi_ssid, config.wifi_secret)

	for count in range(10):
		if wlan.isconnected():
			break

		info("waiting for {} ...".format(config.wifi_ssid))
		
		for i in range(5):
			on_led.write()
			sleep(.1)
			off_led.write()
			sleep(.1)

	if count < 9:
		info("Connected!")
	else:
		error("Not connected!")


	while True:
		try:
			while wlan.isconnected():
				wifi_connected.set()
				versions["ipv4"] = list(wlan.ifconfig())[0]
				versions["signal"] = wlan.status('rssi')
				await asyncio.sleep(1)
			await asyncio.sleep(1)
			if wlan.isconnected():
				continue
			wifi_connected.clear()
			if retries > 3:
				error("wifi: not connecting - hard reset")
				reboot(0)
			else:
				info("wifi({}): connecting to {}".format(retries, config.wifi_ssid))
				retries += 1
			if essid == '':
				wlan.connect(config.wifi_ssid, config.wifi_secret)
			else:
				wlan.connect()
			await asyncio.sleep(2)
		except asyncio.CancelledError:
			return
		except Exception as e:
			error("wifi: error: {}".format(e) )
			error("wifi: restarting wlan")
			wlan.disconnect()
			wlan.active(False)
			await asyncio.sleep(1)
			wlan.active(True)
			info("wifi: connected!")
	
	exited("wifi disabled")
	wlan.disconnect()
	wlan.active(False)

asyncio.create_task(wifi())
