# alog.py

version = (2, 0, 10)
# 2010: renamed alog.py to core.py, moved a lot out of main to here

from machine import RTC, Pin, reset, freq
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

try:
	import webrepl
	webrepl_loaded = True
except:
	webrepl_loaded = False

wifi_connected = asyncio.Event()
webrepl_connected = asyncio.Event()
# start as connected for booting
webrepl_connected.set()

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

###################
# Turn off AP mode
###################
		
WLAN(AP_IF).active(False)

espMAC = str(ubinascii.hexlify(WLAN().config('mac')).decode() )
rtc = RTC()

def load_config(name=espMAC, instance="run"):
	try:
		full = {}
		with open(name) as file:
			raw = file.readline()
			while raw:
				kv = loads(raw)
				if instance and instance in kv:
					return kv[instance]
				full.update(kv)
				raw = file.readline()
		return full
	except:
		error("load_file: {} failed.".format(name))
		return {}

###################
# Look for hostname
###################

try:
	hostname = load_config()
except:
	hostname = espMAC

# log = 0 no output,1+=error 3+=info 5+=debug
def debug(msg, value=""):
	if webrepl_connected.is_set():
		if 6 <= flag.get('log'):
			# print('\u001b[36m', msg, value, "\u001b[0m" )
			info(msg, lev=6, color='\u001b[36m')

def error(msg):
	info(msg, lev=0, color='\u001b[31m', end="\n")

def info(msg, lev=2, color='\u001b[0m', end="\n"):
	if lev <= flag.get('log'):
		dt = offset_time()
		print("{}{:02d}:{:02d}:{:02d}: {}: {}: {}{}".format( color,
			dt[3], dt[4], dt[5], mem_free(), hostname, 
			msg, "\u001b[0m" ), end=end )


info("hostname: {} ({})".format(hostname, freq()) )

#########################
# Check for webrepl connections
#########################

async def webrepl_status():
	started("webrepl_status handler")
	await asyncio.sleep(30)
	while webrepl_loaded:
		# wait until webrepl connection is no longer established
		webrepl_connected.set()
		info("webrepl_status: connected")
		while hasattr(webrepl.client_s, "fileno") and webrepl.client_s.fileno() > 0:
			await asyncio.sleep(10)
		info("webrepl_status: not connected - disabling output")
		webrepl_connected.clear()
		while not hasattr(webrepl.client_s, "fileno") or webrepl.client_s.fileno() < 0:
			await asyncio.sleep(1)

#########################
# Turn on wifi (initial)
#########################

wlan = WLAN(STA_IF)
wlan.active(True)
# sleep to stop from rebooting constantly on esp32?
sleep(.5)
wlan.config(dhcp_hostname=hostname)
# pm=2 is PM_POWERSAVE
# wlan.config(pm=2)
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

async def blink():
	statusled = Pin(2, Pin.OUT, 0)
	# 200 is wifi not connected
	status = 200
	while True:
		statusled.value(0)
		await asyncio.sleep_ms(status)
		statusled.value(1)
		await asyncio.sleep_ms(status)
		sleep(.05)
		if wlan.isconnected():
			status = 3000
		else:
			status = 200

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


def offset_time():
	return localtime(time() + ((flag.get("timezone") - 24) * 3600) )

def started(pid):
	info("started: {}".format(pid))
def running(pid):
	info("running: {}".format(pid))
def stopped(pid):
	debug("stopped.")
def exited(pid):
	info("exited: {}".format(pid))


# saves file in json format, separate lines to allow for reading partial config (above)
# TODO: combine with a setup script to allow configuration via web/AP mode?

def save_json(name, content) -> bool:
	try:
		with open(name, "w") as file:
			for k,v in content.items():
				file.write(dumps({k:v}) )
				file.write("\n")
		info('Saved config {}'.format(name))
		return True
	except:
		error('save_file: {} failed'.format(name))
		return False

asyncio.create_task(blink())
asyncio.create_task(wifi())
asyncio.create_task(webrepl_status())

