# wifi.py

from versions import versions
versions[__name__] = 12
# 10: refactored
# 11: added global versions to fix info not being added
# 12: enabled ap_mode on suspect wifi config, added exception handling to wifi_connect,
#     don't wait for config change, keep checking for wifi connection, reconnect fully every minute

from network import WLAN, STA_IF, AP_IF, STAT_NO_AP_FOUND, STAT_WRONG_PASSWORD, STAT_GOT_IP, STAT_CONNECTING
from time import sleep, sleep_ms, ticks_ms
from system import config, start, reboot
from logger import info, error, debug
from blinkled import on_led, off_led, wifi_status
from events import wifi_connected, config_changed, low_power
import socket

wifi_codes = {
		1000: "STAT_IDLE",
		1001: "STAT_CONNECTING",
		1010: "STAT_GOT_IP",
		200: "STAT_BEACON_TIMEOUT",
		201: "STAT_NO_AP_FOUND",
		202: "STAT_WRONG_PASSWORD",
		203: "STAT_CONNECT_FAIL",
		204: "STAT_HANDSHAKE_TIMEOUT",
		210: "STAT_NO_AP_FOUND_W_COMPATIBLE_SECURITY",
		211: "STAT_NO_AP_FOUND_IN_AUTHMODE_THRESHOLD",
		212: "STAT_NO_AP_FOUND_IN_RSSI_THRESHOLD"
		}

import asyncio

# disable AP mode to start (only enable if can't connect as client)
ap_wlan = WLAN(AP_IF)
ap_wlan.active(False)

info("wifi: hostname: {}".format(config.hostname) )
info("wifi: ssid: {}".format(config.wifi_ssid) )

wlan = WLAN(STA_IF)
wlan.active(False)

# add blinkled to event loop
asyncio.create_task(wifi_status(wlan))

essid = wlan.config('essid')
retries = 0

def wifi_connect():
	# don't connect if no ssid given
	if config.wifi_ssid != "":
		# if wifi name is same and already connected, don't reconnect
		if config.wifi_ssid == essid and wlan.isconnected() and wlan.config('dhcp_hostname') == config.hostname:
			return
		try:
			wlan.active(True)
			sleep(0.5)
			wlan.disconnect()
			wlan.config(dhcp_hostname=config.hostname)

			# Connect to configured network with creds only if something changed or initial boot
			if config.wifi_ssid != essid or config_changed.is_set():
				wlan.connect(config.wifi_ssid, config.wifi_secret)
			else:
				wlan.connect()
		except:
			reboot(10)

wifi_connect()

def suspect_wifi_config() -> bool:

	if config.wifi_ssid == "":
		return True

	if wlan.status() == STAT_WRONG_PASSWORD:
		return True

	# No AP and not connected to the same ssid since power on
	if wlan.status() == STAT_NO_AP_FOUND and config.last_wifi_ssid != config.wifi_ssid:
		return True

	return False

async def wifi():
	global versions
	global wlan
	global config
	global wifi_connected
	wifi_connected.clear()

	# If wifi was configured, wait for 30 seconds (only at startup) before retrying a full connect

	retries = 0
	
	error("wifi: handler started")

	while retries < 10 and wlan.status() == STAT_CONNECTING:
		retries += 1
		debug("wifi: waiting for {} ({}) ...".format(config.wifi_ssid, retries))
		await asyncio.sleep(3)

	retries = 0
	while True:
		# try:
			while wlan.isconnected() and wlan.status() == STAT_GOT_IP:
				
				# set last known good wifi in non-persistent memory
				# used later to determine if wifi suspected to be misconfigured
				# if it worked since the last boot, probably still good
				# wait for it to come back online, could be wireless rebooting

				config.last_wifi_ssid = config.wifi_ssid

				if not wifi_connected.is_set(): 
					retries = 0
					wifi_connected.set()
					info("wifi: connected to {} !".format(config.wifi_ssid) )

					versions["ipv4"] = list(wlan.ifconfig())[0]
					versions["signal"] = wlan.status('rssi')
				
				if config.hostname != wlan.config('dhcp_hostname'):
					error("wifi: changing hostname from {} to {}".format(wlan.config('dhcp_hostname'), config.hostname))
					retries = 0
					wlan.disconnect()

				await asyncio.sleep(1)
			
			await asyncio.sleep(1)

			# Just in case there was a blip, do not need to reconnect
			if wlan.isconnected() and wlan.status() == STAT_GOT_IP:
				continue
			
			error(f"wifi: not connected: {wifi_codes[wlan.status()]}" )
			wifi_connected.clear()

			# Handle a bad password or missing wifi name or AP not found since power on
			# by waiting for a config change (need need to keep trying to connect)
			# if you power on and AP is not found, the device will try to keep reconnecting

			# if suspect_wifi_config():

			# 	config_changed.clear()
			# 	error("wifi: suspected bad wifi config, waiting for config change")
			# 	await config_changed.wait()
				
			# Try 150 times or about 5 minutes before rebooting
			if retries > 150:
				error("wifi: not connecting - hard reset")
				reboot(0)
			else:
				info("wifi: connecting to {} ({}) ...".format(config.wifi_ssid, retries))
				retries += 1

			# reconnect fully every minute
			if retries % 30 == 0:
				wifi_connect()
			
			await asyncio.sleep(2)

		# except Exception as e:
		# 	error("wifi: error: {}".format(e) )
		# 	error("wifi: restarting wlan")
		# 	wlan.disconnect()
		# 	wlan.active(False)
		# 	await asyncio.sleep(1)
		# 	wlan.active(True)
	
start(wifi)

def start_ap_mode():
	global ap_wlan
	global low_power
	low_power.set()

	ap_wlan.active(True)
	# set ESSID and password; WPA2 minimum length is 8
	ap_wlan.config(essid=config.hostname, password="12342345")

def stop_ap_mode():
	global ap_wlan
	global low_power
	low_power.clear()

	ap_wlan.active(False)

async def ap_wifi_handler():
	global ap_wlan
	global config

	while True:
		try:
			if suspect_wifi_config():
				# clear this flag so and wait until wifi is configured
				config_changed.clear()
				error("wifi: bad password or wifi not configured, starting AP mode")
				start_ap_mode()
				await asyncio.sleep(5)
				if not ap_wlan.active():
					error("wifi: failed to start AP mode, restarting")
					reboot(10)
				ap_ip = ap_wlan.ifconfig()[0]
				info("ap_wifi_handler: Active - using IP address: {}".format(ap_ip) )
				info("ap_wifi_handler: waiting for client wifi to connect")

				await captive_portal(ap_ip)

				info("wifi: stopping AP mode")
				stop_ap_mode()

		except asyncio.CancelledError:
			reboot(10)
		
		await asyncio.sleep(5)

start(ap_wifi_handler)

# start dns server for captive portal and wait for client wifi to connect
# dns needs AP mode enabled, so this can't start until ap_mode is enabled
# and should be stopped before ap_mode is stopped
async def captive_portal(ip):
	ip_bytes = bytes(map(int, ip.split(".")))
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.setblocking(False)  # non-blocking mode
		s.bind(("0.0.0.0", 53))
	except Exception as e:
		error("captive_portal: fatal: bind error: {}".format(e) )
		return

	debug("DNS server listening on port 53, redirecting queries to {}".format(ip) )

	while not wifi_connected.is_set():
		try:
			data, addr = s.recvfrom(512)  # non-blocking -> OSError if no data
		except OSError:
			# no data available
			await asyncio.sleep(0.05)
			continue
		except Exception as e:
			error("captive_portal: recvfrom error: {}".format(e) )
			await asyncio.sleep(0.1)
			continue

		if not data:
			await asyncio.sleep(0.1)
			continue

		# Build a simple DNS response: copy transaction ID, flags, counts, question, and add one A record answer
		try:
			transaction_id = data[0:2]
			flags = b"\x81\x80"  # standard response, recursion not available
			qdcount = data[4:6]  # usually 0x0001
			# set answer count to 1
			ancount = b"\x00\x01"
			nscount = b"\x00\x00"
			arcount = b"\x00\x00"
			header = transaction_id + flags + qdcount + ancount + nscount + arcount
			question = data[12:]
			# Answer: pointer to name (0xc00c), type A (1), class IN (1), TTL 60s, rdlength 4, address
			answer = b"\xc0\x0c" + b"\x00\x01" + b"\x00\x01" + b"\x00\x00\x00\x3c" + b"\x00\x04" + ip_bytes
			resp = header + question + answer
			try:
				s.sendto(resp, addr)
			except Exception as e:
				# ignore send errors (client might have disconnected)
				error("captive_portal: sendto error: {}".format(e) )
		except Exception as e:
			print("captive_portal: packet build error: {}".format(e) )
			await asyncio.sleep(0.1)
			continue
	
	debug("captive_portal: client wifi connected, dns server stopping")
	s.close()

