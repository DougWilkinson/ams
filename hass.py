# hass.py

from versions import versions
versions[__name__] = 3
# 2010: fixed state online not publishing
# 2011: added flag set to track time updates

import flag
import uasyncio as asyncio
from gc import collect
from machine import RTC
import ntptime
from core import wlan, wifi_connected, espMAC, info, error, debug, started, stopped, hostname
from umqtt.simple import MQTTClient
import json
import mysecrets
from msgqueue import MsgQueue
from device import Device

flag.clear("timesynced")
publish_queue = MsgQueue(15)

haconfig_topic = mysecrets.ha_config_prefix + "/{}/{}/config"
topic__template = mysecrets.ha_topic_prefix + "/{}/{}"

client = MQTTClient(espMAC, mysecrets.mqtt_server,
	user=mysecrets.mqtt_user,
	password=mysecrets.mqtt_pass,
	keepalive=60)

client.set_last_will('hass/sensor/esp/{}/state'.format(espMAC), 'offline', retain=True)

mqtt_time_lost = asyncio.Event()
# wifi_connected = asyncio.Event()
mqtt_connected = asyncio.Event()
mqtt_error = asyncio.Event()		# set by pub/sub if error to trigger reconnect
sub_all = asyncio.Event()

subscribed_topics = {}

async def publish_state(device):
	started(device.name)
	while True:
		await device.publish.wait()
		debug("pubstate: {}, {}, pubflag: {}".format(device.name,device.state, device.publish.is_set()))
		publish_queue.put(gen_topic(device,"/state"), device.state.lower() if device.set_lower else device.state)

		if hasattr(device, 'attr'):
			publish_queue.put(gen_topic(device,"/attrs"), json.dumps(device.attr) )
		device.publish.clear()

def gen_topic(device, post=""):
	return "{}/{}/{}{}".format(mysecrets.ha_topic_prefix, device.dtype, device.name, post)

# Notifier used to initialize an HA/MQTT device
# Create HA entity based on dtype
# Create an async task to update state if it changes
# Add to subscribe list if not Read Only
def ha_setup(device):
	info("ha_setup: {}".format(device.name))
	msg = { "name": device.name, '~': gen_topic(device), 'uniq_id': device.name, 'obj_id': device.name, 'stat_t': "~/state",
			'json_attr_t': "~/attrs", "retain": True }
	if device.units:
		msg['unit_of_meas'] = device.units
	if device.dtype == "switch":
		msg['cmd_t'] = "~/set"
	if device.dtype == "cover":
		msg['cmd_t'] = "~/set"
	if device.dtype == "light":
		msg['cmd_t'] = "~/set"
		msg['bri_cmd_t'] = "~_bri/set"
		msg['bri_stat_t'] = "~_bri/state"
		msg['rgb_cmd_t'] = "~_rgb/set"
		msg['rgb_stat_t'] = "~_rgb/state"

	publish_queue.put(haconfig_topic.format(device.dtype, device.name ), json.dumps(msg) )
	asyncio.create_task(publish_state(device))
	ha_sub(device)
	
def ha_sub(device):
	# add msgqueue to dict for callback handling
	if not device.ro:
		subscribed_topics[gen_topic(device,"/set")] = device
	sub_all.set()

# Set last will device here
state = Device('esp/{}'.format(espMAC), "unknown", ro=True, notifier_setup=ha_setup)

# Subscribes and resubs when mqtt connection is lost
async def sub():  # (re)connection.
	started("sub")
	while True:
		try:
			await sub_all.wait()
			await wifi_connected.wait()
			await mqtt_connected.wait()
			client.subscribe('hass/utc')
			for topic in subscribed_topics:
				if '/' in topic:
					info('sub: {}'.format(topic) )
					client.subscribe(topic)
					await asyncio.sleep(1)
			error("sub: All topics resubscribed plus hass/utc")
			sub_all.clear()
		except asyncio.CancelledError:
			stopped("sub")
			return
		except:
			# Signal mqtt reconnect
			mqtt_connected.clear()
			mqtt_error.set()

async def pub():
	global publish_queue
	started("pub")
	while True:
		try:
			async for topic, msg in publish_queue:
				await wifi_connected.wait()
				await mqtt_connected.wait()
				client.publish(topic, msg, retain=True)
				debug("pub: topic: {}".format(topic) )
		except asyncio.CancelledError:
			stopped("pub")
			return
		except:
			mqtt_connected.clear()
			mqtt_error.set()
			error('pub: Error topic {}'.format(topic))
			await asyncio.sleep(1)

# # Keeps wifi connected
# # TODO: Add error handling hard reset
# async def wifi():
# 	started("wifi")
# 	essid = wlan.config('essid')
# 	while True:
# 		try:
# 			while wlan.isconnected():
# 				wifi_connected.set()
# 				await asyncio.sleep(1)
# 			await asyncio.sleep(1)
# 			if wlan.isconnected():
# 				continue
# 			wifi_connected.clear()
# 			info("wifi: connecting to {}".format(mysecrets.wifi_name))
# 			if essid == '':
# 				wlan.connect(mysecrets.wifi_name, mysecrets.wifi_pass)
# 			else:
# 				wlan.connect()
# 			await asyncio.sleep(2)
# 		except asyncio.CancelledError:
# 			stopped("wifi")
# 			return
# 		except:
# 			error("wifi: error, hard reset")
# 			wlan.disconnect()
# 			wlan.active(False)
# 			await asyncio.sleep(1)
# 			wlan.active(True)
# 			info("wifi: connected!")
# 	exited(pid)

# Callback for MQTTClient
def cb(topic, msg):
	td = topic.decode("utf-8")
	if td == "hass/utc":
		j = json.loads(msg)
		if 'UTC' in j:
			RTC().datetime(tuple(int(i) for i in tuple(j['UTC'].split(','))))
			# flag.set("hour", RTC().datetime()[4])
			# flag.set("minute", RTC().datetime()[5])
			# clear watchdog to skip ntp time sync
			mqtt_time_lost.clear()
			flag.set("timesynced")
			debug("hass/utc: time set")
		if "timezone" in j and (flag.get('timezone') - 24) != j['timezone']:
				flag.set('timezone', j['timezone'] + 24 )
				info("hass/utc: timezone set: {}".format(flag.get('timezone')) )
		return

	debug('cb: topic: {}'.format(topic))
	if td in subscribed_topics:
		# subscribed_topics holds the topic and device object
		device = subscribed_topics[td]
		# update device state with new value
		device.set_state(msg.decode("utf-8"))
		# put directly in publish_queue to be published on next await
		device.publish.clear()
		publish_queue.put(gen_topic(device,"/state"), device.state.lower() if device.set_lower else device.state)

# ping mqtt every 30 seconds
async def ping():
	started("ping")
	while True:
		try:
			await mqtt_connected.wait()
			client.ping()
			await asyncio.sleep(30)
		except asyncio.CancelledError:
			stopped("ping")
			return
		except OSError:
			mqtt_connected.clear()
			mqtt_error.set()

# Check for incoming MQTT messages (calls callback if received)
async def check():
	started("check")
	while True:
		try:
			await mqtt_connected.wait()
			client.check_msg()
			await asyncio.sleep(0)
		except asyncio.CancelledError:
			stopped("check")
			return
		except OSError:
			mqtt_connected.clear()
			mqtt_error.set()

# Maintain MQTTclient connection, reconnect if flagged as bad
# TODO: "test" if server is available using sockets
async def mqtt():
	global state
	started("mqtt")
	client.set_callback(cb)
	while True:
		try:
			await wifi_connected.wait()
			#state.attr = { "hostname": hostname, "versions": versions, "mac": espMAC, "ipv4": list(wlan.ifconfig())[0]}
			state.attr = versions
			client.connect(clean_session=True)
			client.ping()
			mqtt_connected.set()
			mqtt_error.clear()
			sub_all.set()
			state.set_state('online')
			state.publish.set()
			info("mqtt: connected")
			await mqtt_error.wait()
		except asyncio.CancelledError:
			stopped("mqtt")
			return
		except OSError:
			error("mqtt: connect OSError")
			await asyncio.sleep(2)

async def ntp():
	started('ntp')
	mysecrets.ntp_servers.append(ntptime.host)
	info("ntpsynctime: servers: {}".format(mysecrets.ntp_servers) )
	while True:
		while not mqtt_time_lost.is_set():
			mqtt_time_lost.set()
			await asyncio.sleep(70)

		for host in mysecrets.ntp_servers:
			flag.clear("timesynced")
			try:
				debug("rtclock: trying ntp host {} ".format(host) )
				ntptime.host = host
				ntptime.settime()
				# flag.set("hour", RTC().datetime()[4])
				# flag.set("minute", RTC().datetime()[5])
				debug("rtclock: success!")
				flag.set("timesynced")
				break
			except OSError:
				error("ntp: Failed!")
				continue
		await asyncio.sleep(70)

handlers = [ mqtt, ping, check, pub, sub, ntp ]

info("hass: start: creating core tasks ...")
# Load core modules
for coro in handlers:
	asyncio.create_task(coro())
collect()
info("hass:start: core tasks created ..." )

