# hass.py

from versions import versions
versions[__name__] = 15
# 10: refactored version with Device changes
# 11: fixed attrs and versions to set last_restart immediately
# 12: moved timezone update for config and localtime to utc handler
# 13: added await_subscribe to wait for wifi and mqtt to connect
# 14: fixed missing binary_sensor in check for HA config
# 15: moved device.configured check to only ha config a device if dtype is right and not already set to True (light_bri and light_rgb)

import asyncio
import time
from gc import collect
from machine import RTC

from logger import info, error, debug
from profiles import espMAC
from system import config, start
from logger import strftime
from localtime import offset_time

from events import wifi_connected, time_synced, mqtt_connected
from events import mqtt_error, subscribe_all, device_added

from umqtt.simple import MQTTClient
import json

from msgqueue import MsgQueue
from device import Device, device_list
from events import config_changed

publish_queue = MsgQueue(50)

haconfig_topic = config.ha_config + "/{}/{}/config"
topic__template = config.ha_topic + "/{}/{}"

client = MQTTClient(espMAC, config.mqtt_server,
	port=0,
	ssl=False,
	ssl_params={},
	user=config.mqtt_username,
	password=config.mqtt_password,
	keepalive=60)

client.set_last_will('hass/sensor/esp/{}/state'.format(espMAC), 'offline', retain=True)

# wifi_connected = asyncio.Event()

# place for all subscribed topics and related device objects
subscribed_topics = {}

def gen_topic(device, post=""):
	return "{}/{}/{}{}".format(config.ha_topic, device.dtype, device.name, post)

async def publish_state(device: Device):
	info("hass: {}: publish_state_handler running".format(device.name) )
	while True:
		await device.needs_publishing.wait()

		debug("pubstate: device: {} state: {}".format(device.name, device.state) )

		# publish state using name only as topic (if "mqtt") or generated HA topic (all others)

		if device.dtype == "mqtt":
			pub_topic = device.name
		else:
			pub_topic = gen_topic(device)

		publish_queue.put(pub_topic + "/state", device.state.lower() if device.set_lower else device.state)

		if hasattr(device, 'attrs'):
			publish_queue.put(pub_topic + "/attrs", json.dumps(device.attrs) )

		device.needs_publishing.clear()


# Create HA entity based on dtype
# Create an async task to update state if publish flag is True
# Add to subscribe list if subscribe flag is True
async def device_handler():
	global subscribed_topics
	info("hass: device_handler running")
	while True:
		await device_added.wait()
		device_added.clear()
		info("hass: maintain_devices: new device added")

		for device_name, device in device_list.items():

			# Add to subscribe list if True
			if device.subscribe:
				if device.dtype == "mqtt":
					topic = device.name
				else:
					topic = gen_topic(device, "/set")
				
				# save in dictionary with device object for use in callback
				subscribed_topics[topic] = device

				# subscribe now
				asyncio.create_task(await_subscribe(topic) )

			# Create publisher task only if publish is True
			if device.publish:
				asyncio.create_task(publish_state(device))

			if device.configured:
				continue
							
			# remaining steps only if we want to configure device in HA

			if device.dtype not in "binary_sensor|sensor|switch|cover|light":
				device.configured = True
				continue
			
			info("hass: device setup: {}: {}".format(device.dtype, device.name))

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
			device.configured = True
			
	
# Set last will device here
versions['last_restart'] = strftime()
state = Device('esp/{}'.format(espMAC), "unknown", needs_publishing=True)
state.attrs = versions

async def await_subscribe(topic):
	await wifi_connected.wait()
	await mqtt_connected.wait()
	subscribe_topic(topic)
								
def subscribe_topic(topic):
	try:
		client.subscribe(topic)
		info('hass: subscribed: {}'.format(topic) )
	except:
		error('hass: subscribe failed: {}'.format(topic) )
		mqtt_error.set()

# Subscribes and resubs when mqtt connection is lost
async def subscribe_all_handler():

	info("hass: subscribe_all_handler running")

	while True:
		try:
			await subscribe_all.wait()
			info("hass: sub_all: resubscribe pending wifi/mqtt reconnect")
			await wifi_connected.wait()
			await mqtt_connected.wait()
			
			# should be done as part of the devices
			# client.subscribe('hass/utc')

			for topic in subscribed_topics:
				subscribe_topic(topic)
								
			info("hass: sub_all: resubscribe scheduled all devices")
			
			subscribe_all.clear()
		except Exception as e:
			error("hass: ping: {}".format(e) )
			# Signal mqtt reconnect
			mqtt_connected.clear()
			mqtt_error.set()

async def publish_handler():
	global publish_queue
	info("hass: publish_handler running")
	while True:
		async for pubitem in publish_queue:
			try:
				topic, msg = pubitem
				debug("pub: topic: {}".format(topic) )
				await wifi_connected.wait()
				await mqtt_connected.wait()
				client.publish(topic, msg, retain=True)
			except ValueError:
				error('pub: ValueError unpacking {}'.format(pubitem))
			except Exception as e:
				error("hass: publish: {}".format(e) )
				mqtt_connected.clear()
				mqtt_error.set()
				error('pub: Error topic {}'.format(topic))
				await asyncio.sleep(1)

utc = Device('hass/utc', "unknown", dtype="mqtt", publish=False)

async def utc_handler():
	info("hass: utc_handler running")
	while True:
		async for _, utc_state in utc.q:
			try:
				j = json.loads(utc_state)
				if 'UTC' in j:
					RTC().datetime(tuple(int(i) for i in tuple(j['UTC'].split(','))))
					# flag.set("hour", RTC().datetime()[4])
					# flag.set("minute", RTC().datetime()[5])
					# clear watchdog to skip ntp time sync
					time_synced.set()
					config.timesync_secs = time.time()
					#debug("UTC: {}".format(j['UTC']) )

				if "timezone" in j and (config.timezone - 24) != j['timezone']:
						config.timezone = j['timezone'] + 24
						offset_time(config.timezone)
						config_changed.set()
						config.save()
						debug("timezone updated: {}".format(config.timezone) )
			except:
				error('handle_utc: Error processing utc: {}'.format(state))

# Callback for MQTTClient
def cb(topic, msg):
	#debug('cb: topic: {}'.format(topic))
	global state
	td = topic.decode("utf-8")

	if 'esp/{}'.format(espMAC) in td:
		client.set_last_will('hass/sensor/esp/{}/state'.format(espMAC), 'shutdown', retain=True)

	if td in subscribed_topics:
		# get the device object to update it
		device = subscribed_topics[td]
		
		# update device state with new value
		device.set_state(msg.decode("utf-8"))
		
		# put directly in publish_queue to be published on next await
		if device.publish:
			device.needs_publishing.clear()
			publish_queue.put(gen_topic(device,"/state"), device.state.lower() if device.set_lower else device.state)

# ping mqtt every 30 seconds
async def ping_handler():
	info("hass: ping_handler running")
	while True:
		try:
			await mqtt_connected.wait()
			client.ping()
			await asyncio.sleep(30)
		except Exception as e:
			error("hass: ping: {}".format(e) )
			mqtt_connected.clear()
			mqtt_error.set()

# Check for incoming MQTT messages (calls callback if received)
async def check_msg_handler():
	info("hass: check_msg_handler running")
	while True:
		try:
			await mqtt_connected.wait()
			client.check_msg()
			await asyncio.sleep(0)
		except Exception as e:
			error("hass: check_msg: {}".format(e) )
			mqtt_connected.clear()
			mqtt_error.set()

# Maintain MQTTclient connection, reconnect if flagged as bad
# TODO: "test" if server is available using sockets
async def mqtt_connection_handler():
	global state
	info("hass: mqtt_connection_handler running")
	client.set_callback(cb)

	while True:
		try:

			if not config.mqtt_server or not config.mqtt_username:
				error("hass: mqtt: waiting for mqtt_server / mqtt_username to be configured")
				await config_changed.wait()
				continue

			try:
				if config.mqtt_ssl:
					client.port = 8883
					ssl_params = {'server_hostname': config.mqtt_server}
				else:
					client.port = 1883
					ssl_params = {}

				client.ssl = config.mqtt_ssl
				client.server = config.mqtt_server
				client.user = config.mqtt_username
				client.pswd = config.mqtt_password
				client.ssl_params = ssl_params

			except:
				error("hass: mqtt: bad mqtt config options - waiting for config change")
				await config_changed.wait()
				continue

			info("hass: mqtt_server: {}".format(config.mqtt_server) )
			info("hass: mqtt_ssl: {}".format(config.mqtt_ssl) )

			await wifi_connected.wait()
			state.attrs = versions
			client.connect(clean_session=True)
			client.ping()
			mqtt_connected.set()
			mqtt_error.clear()
			subscribe_all.set()
			state.set_state('online')
			state.needs_publishing.set()
			info("mqtt: connected: {}".format(config.mqtt_server) )
			await mqtt_error.wait()
		except Exception as e:
			error("hass: mqtt_connect_handler: {}".format(e) )
			error("mqtt: connect OSError")
			await asyncio.sleep(2)

# async def ntp():
# 	start('ntp_time_sync')
# 	config.ntp_servers.append(ntptime.host)
# 	info("ntpsynctime: servers: {}".format(config.ntp_servers) )
# 	while True:
# 		while not mqtt_time_lost.is_set():
# 			mqtt_time_lost.set()
# 			await asyncio.sleep(70)

# 		for host in config.ntp_servers:
# 			config.timesynced = 0
# 			try:
# 				debug("rtclock: trying ntp host {} ".format(host) )
# 				ntptime.host = host
# 				ntptime.settime()
# 				# flag.set("hour", RTC().datetime()[4])
# 				# flag.set("minute", RTC().datetime()[5])
# 				debug("rtclock: success!")
# 				config.timesynced = 1
# 				break
# 			except OSError:
# 				error("ntp: Failed!")
# 				continue
# 		await asyncio.sleep(70)

start(mqtt_connection_handler)
start(ping_handler)
start(check_msg_handler)
start(publish_handler)
start(subscribe_all_handler)
start(utc_handler)
start(device_handler)

info("hass: setup complete" )

