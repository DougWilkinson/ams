# hass.py

# main.py

version = ( 1, 0, 0)

from network import WLAN, AP_IF, STA_IF
WLAN(AP_IF).active(False)
wlan = WLAN(STA_IF)
wlan.active(True)

import asyncio
from gc import mem_free, collect
from time import localtime, time, sleep
from machine import RTC, reset
import ntptime
from alog import espMAC, info, error, debug, started, stopped, exited
from umqtt.simple import MQTTClient
import json
import mysecrets
from msgqueue import MsgQueue

publish_queue = MsgQueue(15)

haconfig_topic = mysecrets.ha_config_prefix + "/{}/{}/config"
topic__template = mysecrets.ha_topic_prefix + "/{}/{}"

client = MQTTClient(espMAC, mysecrets.mqtt_server,
	user=mysecrets.mqtt_user,
	password=mysecrets.mqtt_pass,
	keepalive=60)

wifi_connected = asyncio.Event()
mqtt_connected = asyncio.Event()
mqtt_error = asyncio.Event()		# set by pub/sub if error to trigger reconnect
sub_all = asyncio.Event()

subscribed_topics = {}

async def publish_state(device):
	started(device.name)
	while True:
		await device.publish.wait()
		# info("pubstate: {}, {}".format(device.name,device.state))
		if device.dtype == "binary_sensor":
			state = "ON" if device.state else "OFF"
		else:
			state = str(device.state)
		publish_queue.put(gen_topic(device,"/state"), state)
		device.publish.clear()

def gen_topic(device, post=""):
	return "{}/{}/{}{}".format(mysecrets.ha_topic_prefix, device.dtype, device.name, post)

def ha_setup(device):
	info("setup: {}".format(device.name))
	msg = { "name": device.name, '~': gen_topic(device), 'uniq_id': device.name, 'obj_id': device.name, 'stat_t': "~/state",
			'json_attr_t': "~/attrs", "retain": True }
	if device.units:
		msg['unit_of_meas'] = device.units
	if device.dtype == "switch":
		msg['cmd_t'] = "~/set"
	if device.dtype == "cover":
		msg['cmd_t'] = "~/set"
		msg['pos_t'] = "~_position/state"
	if device.dtype == "light":
		msg['cmd_t'] = "~/set"
		msg['bri_cmd_t'] = "~_bri/set"
		msg['bri_stat_t'] = "~_bri/state"
		msg['rgb_cmd_t'] = "~_rgb/set"
		msg['rgb_stat_t'] = "~_rgb/state"

	publish_queue.put(haconfig_topic.format(device.dtype, device.name ), json.dumps(msg) )
	asyncio.create_task(publish_state(device))
	# add msgqueue to dict for callback handling
	if not device.ro:
		subscribed_topics[gen_topic(device,"/set")] = device.setstate
	sub_all.set()

# class Sensor:
# 	def __init__(self, device) -> None:
# 		setup(device, "sensor")

# class Light:
# 	def __init__(self, device) -> None:
# 		setup(device, "light")

# class Switch:
# 	def __init__(self, device) -> None:
# 		setup(device, "switch")

# class BinarySensor:
# 	def __init__(self, device) -> None:
# 		setup(device, "binary_sensor")

# class Cover:
# 	def __init__(self, device) -> None:
# 		setup(device, "cover")

# Subscribes and resubs when mqtt connection is lost
async def subscriber(pid):  # (re)connection.
	started(pid)
	while True:
		try:
			await sub_all.wait()
			await wifi_connected.wait()
			await mqtt_connected.wait()
			for topic in subscribed_topics:
				if '/' in topic:
					info('subscriber: {}'.format(topic) )
					client.subscribe(topic)
					await asyncio.sleep(1)
			error("subscriber: All topics resubscribed")
			sub_all.clear()
		except asyncio.CancelledError:
			stopped(pid)
			return
		except:
			# Signal mqtt reconnect
			mqtt_connected.clear()
			mqtt_error.set()
	exited(pid)

async def publisher(pid):
	global publish_queue
	started(pid)
	while True:
		try:
			async for topic, msg in publish_queue:
				await wifi_connected.wait()
				await mqtt_connected.wait()
				client.publish(topic, msg, retain=True)
				# info("publisher: {}".format(topic) )
		except asyncio.CancelledError:
			stopped(pid)
			return
		except:
			mqtt_connected.clear()
			mqtt_error.set()
			error('pub: Error during {}'.format(topic))
			await asyncio.sleep(1)

# Keeps wifi connected
# TODO: Add error handling hard reset
async def wifi(pid):
	started(pid)
	essid = wlan.config('essid')
	while True:
		try:
			while wlan.isconnected():
				wifi_connected.set()
				await asyncio.sleep(1)
			await asyncio.sleep(1)
			if wlan.isconnected():
				continue
			wifi_connected.clear()
			info("wifi: connect {}".format(mysecrets.wifi_name))
			if essid == '':
				wlan.connect(mysecrets.wifi_name, mysecrets.wifi_pass)
			else:
				wlan.connect()
			await asyncio.sleep(2)
		except asyncio.CancelledError:
			stopped(pid)
			return
		except:
			error("wifi: error - restarting")
			wlan.disconnect()
			wlan.active(False)
			await asyncio.sleep(1)
			wlan.active(True)
			debug("wifi: activated")
	exited(pid)

# Callback for MQTTClient
def msg_cb(topic, msg):
	info('cb: {}'.format(topic))
	td = topic.decode("utf-8")
	if td in subscribed_topics:
		# holds setstate MsgQueue, so put directly to device here
		subscribed_topics[td].put(td, msg.decode("utf-8"))

# ping mqtt every 30 seconds
async def mqtt_ping(pid):
	started(pid)
	while True:
		try:
			await mqtt_connected.wait()
			client.ping()
			await asyncio.sleep(30)
		except asyncio.CancelledError:
			stopped(pid)
			return
		except OSError:
			mqtt_connected.clear()
			mqtt_error.set()
	exited(pid)

# Check for incoming MQTT messages (calls callback if received)
async def mqtt_check(pid):
	started(pid)
	while True:
		try:
			await mqtt_connected.wait()
			client.check_msg()
			await asyncio.sleep(0)
		except asyncio.CancelledError:
			stopped(pid)
			return
		except OSError:
			mqtt_connected.clear()
			mqtt_error.set()
	exited(pid)

# Maintain MQTTclient connection, reconnect if flagged as bad
# TODO: "test" if server is available using sockets
async def mqtt_connection(pid):
	started(pid)
	client.set_callback(msg_cb)
	while True:
		try:
			await wifi_connected.wait()
			client.connect(clean_session=True)
			client.ping()
			mqtt_connected.set()
			mqtt_error.clear()
			sub_all.set()
			await mqtt_error.wait()
		except asyncio.CancelledError:
			return
		except OSError:
			error("mqtt: connect error")
			await asyncio.sleep(2)
	exited(pid)

handlers = {
		'wifi': wifi,
		'mqtt_connection': mqtt_connection,
		'mqtt_ping': mqtt_ping,
		'mqtt_check': mqtt_check,  
		# 'rtclock': rtclock, 
		'publisher': publisher,
		'subscriber': subscriber }

async def start():
	started("loading core modules ...")
	# Load core modules
	for _pid, coro in handlers.items():
		asyncio.create_task(coro(_pid))
	collect()
	error("hass:start: awaiting core modules ..." )
	await asyncio.sleep(5)
		

#asyncio.run(main(handlers))