# main.py
version = (2, 0, 7)
# 2,0,1: added safeboot and flag import
#2,0,2: moved wifi here

import flag
from alog import wlan, wifi_connected, info, error, started, stopped, hostname, espMAC
import uasyncio as asyncio
from machine import reset
from time import sleep
from mysecrets import wifi_name, wifi_pass
from network import WLAN, AP_IF, STA_IF

WLAN(AP_IF).active(False)

info("main: using hostname: {}".format(hostname) )

wlan.active(True)
# sleep to stop from rebooting constantly on esp32?
sleep(.5)
wlan.config(dhcp_hostname=hostname)
wlan.disconnect()
wlan.connect(wifi_name, wifi_pass)

# wait for reconnect to avoid watchdog timeout/reset

for count in range(10):
	if wlan.isconnected():
		break
	info("waiting for {} ...".format(wifi_name))
	sleep(1)

if count < 9:
	info("Connected!")
else:
	error("Not connected!")

#safeboot
def sb():
	reboot(2)

def reboot(boot=10):
	flag.set('boot',boot)
	print("REBOOTING\r\n>>> ")
	for i in range(boot):
		print(i)
		sleep(1)
				 
	reset()
	while True:
		pass

# Keeps wifi connected
async def wifi():
	global wlan
	started("wifi")
	essid = wlan.config('essid')
	retries = 0
	while True:
		try:
			while wlan.isconnected():
				wifi_connected.set()
				await asyncio.sleep(1)
			await asyncio.sleep(1)
			if wlan.isconnected():
				continue
			wifi_connected.clear()
			if retries > 3:
				error("wifi: not connecting - hard reset")
				reboot(0)
			else:
				info("wifi({}): connecting to {}".format(retries, wifi_name))
				retries += 1
			if essid == '':
				wlan.connect(wifi_name, wifi_pass)
			else:
				wlan.connect()
			await asyncio.sleep(2)
		except asyncio.CancelledError:
			stopped("wifi")
			return
		except:
			error("wifi: error, hard reset")
			wlan.disconnect()
			wlan.active(False)
			await asyncio.sleep(1)
			wlan.active(True)
			info("wifi: connected!")
	exited(pid)

asyncio.create_task(wifi())

# load_config() has at minimum a hostname to tell main.py what to import/start

def run():
	mod = __import__(hostname)
	asyncio.run(mod.start(hostname))

if flag.get('boot') == 0:
	run()