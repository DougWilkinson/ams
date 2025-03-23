# core.py

from versions import versions
versions[__name__] = 7
# reordered and introduced minimal keyword

try:
	import webrepl
	webrepl_loaded = True
except:
	webrepl_loaded = False


from machine import RTC, Pin, reset, freq
from platform import platform
from time import localtime, time, sleep
from network import WLAN, STA_IF
from gc import mem_free
import flag
import uasyncio as asyncio
from json import loads, dumps
from mysecrets import wifi_name, wifi_pass
from network import WLAN, AP_IF, STA_IF
import uhashlib
import ubinascii
import uos as os

# set boot to delay startup for 30 seconds unless reboot() used
# gives you a chance to fix issues for low memory
# flag.set('boot',1)

###################
# Wifi 
###################

# Used to signal wifi status in coros
wifi_connected = asyncio.Event()

# disable AP mode
WLAN(AP_IF).active(False)

# build MAC address to use as name if hostname not set
espMAC = str(ubinascii.hexlify(WLAN().config('mac')).decode() )

def load_config(name=espMAC, key="run"):
	try:
		full = {}
		with open(name) as file:
			raw = file.readline()
			while raw:
				kv = loads(raw)
				if key and key in kv:
					return kv[key]
				full.update(kv)
				raw = file.readline()
		return full
	except:
		error("load_file: {} failed.".format(name))
		return {}

# Look for hostname

try:
	hostname = load_config()
except:
	hostname = espMAC

versions["hostname"] = hostname
versions["mac"] = espMAC
versions["freq"] = freq() / 1000000
versions['mpy'] = platform().split('-')[1]

rtc = RTC()

# used for a do nothing loop wait_for
latch = asyncio.Event()

def genhash(file):
	file_hash = uhashlib.sha256()
	with open(file, "rb") as handle:
		buf = handle.read(100)
		while buf:
			file_hash.update(buf)
			buf = handle.read(100)	
	print(ubinascii.hexlify(file_hash.digest() ) )

def offset_time():
	return localtime(time() + ((flag.get("timezone") - 24) * 3600) )
# log = 0 no output,1+=error 3+=info 5+=debug
def debug(msg, value=""):
	if 6 <= flag.get('log'):
		# print('\u001b[36m', msg, value, "\u001b[0m" )
		info(msg, lev=6, color='\u001b[36m')

def error(msg):
	info(msg, lev=0, color='\u001b[31m', end="\n")

def info(msg, lev=2, color='\u001b[0m', end="\n"):
	if lev <= flag.get('log'):
		# get time with offset
		dt = offset_time()
		print("{}{:02d}:{:02d}:{:02d}: {}: {}: {}{}".format( color,
			dt[3], dt[4], dt[5], mem_free(), hostname, 
			msg, "\u001b[0m" ), end=end )


info("hostname: {} ({})".format(hostname, freq()) )

#########################
# Turn on wifi (initial)
#########################

wlan = WLAN(STA_IF)
wlan.active(True)
# sleep to stop from rebooting constantly on esp32?
sleep(.5)
wlan.config(dhcp_hostname=hostname)


wlan.disconnect()
wlan.connect(wifi_name, wifi_pass)

for count in range(10):
	if wlan.isconnected():
		break
	info("waiting for {} ...".format(wifi_name))
	sleep(1)

if count < 9:
	info("Connected!")
else:
	error("Not connected!")

# pm=PM_NONE will never turn radio off, better pings for esp32
# not implemented on 8266, but still allows setting this
# pm=2 is PM_POWERSAVE
# wlan.config(pm=wlan.PM_NONE)

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
				versions["ipv4"] = list(wlan.ifconfig())[0]
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
			return
		except:
			error("wifi: error, hard reset")
			wlan.disconnect()
			wlan.active(False)
			await asyncio.sleep(1)
			wlan.active(True)
			info("wifi: connected!")
	exited("wifi disabled")
	wlan.disconnect()
	wlan.active(False)

def started(pid):
	info("started: {}".format(pid))

asyncio.create_task(wifi())

if "ESP32S2" in os.uname().machine:
	from esp32s2 import blink
if "ESP32S3" in os.uname().machine:
	from esp32s3 import blink
if "ESP8266" in os.uname().machine or "ESP32 " in os.uname().machine:
	from espdev import blink

try:
	asyncio.create_task(blink(wlan))
except:
	pass
