# hass.py

from versions import versions
versions[__name__] = 4
# 2010: fixed state online not publishing
# 2011: added flag set to track time updates

# import flag
import asyncio
import time
from gc import collect
from machine import RTC

from logger import info, error, debug
from profiles import espMAC
from system import config, start
from logger import strftime

from events import wifi_connected, time_synced

from umqtt.simple import MQTTClient
import json

from msgqueue import MsgQueue
from device import Device
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
mqtt_connected = asyncio.Event()
mqtt_error = asyncio.Event()		# set by pub/sub if error to trigger reconnect
sub_all = asyncio.Event()

subscribed_topics = {}

async def publish_state(device):
	info("hass: {}: publish_state_handler running".format(device.name) )
	while True:
		await device.publish.wait()
		debug("pubstate: {}, {}, pubflag: {}".format(device.name,device.state, device.publish.is_set() ) )
		publish_queue.put(gen_topic(device,"/state"), device.state.lower() if device.set_lower else device.state)

		if hasattr(device, 'attr'):
			publish_queue.put(gen_topic(device,"/attrs"), json.dumps(device.attr) )
		device.publish.clear()

def gen_topic(device, post=""):
	return "{}/{}/{}{}".format(config.ha_topic, device.dtype, device.name, post)

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

def subscribe_name(device):
	# add device name for callback handling
	subscribed_topics[device.name] = device

# Set last will device here
state = Device('esp/{}'.format(espMAC), "unknown", notifier_setup=ha_setup)

# Subscribes and resubs when mqtt connection is lost
async def sub():  # (re)connection.
	info("hass: mqtt_subscribe_handler running")
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
			return
		except:
			# Signal mqtt reconnect
			mqtt_connected.clear()
			mqtt_error.set()

async def pub():
	global publish_queue
	info("hass: mqtt_publish_handler running")
	while True:
		async for pubitem in publish_queue:
			try:
				topic, msg = pubitem
				debug("pub: topic: {}".format(topic) )
				await wifi_connected.wait()
				await mqtt_connected.wait()
				client.publish(topic, msg, retain=True)
			except asyncio.CancelledError:
				return
			except ValueError:
				error('pub: ValueError unpacking {}'.format(pubitem))
			except:
				mqtt_connected.clear()
				mqtt_error.set()
				error('pub: Error topic {}'.format(topic))
				await asyncio.sleep(1)

# Callback for MQTTClient
def cb(topic, msg):
	#debug('cb: topic: {}'.format(topic))
	global state
	td = topic.decode("utf-8")
	if td == "hass/utc":
		j = json.loads(msg)
		if 'UTC' in j:
			RTC().datetime(tuple(int(i) for i in tuple(j['UTC'].split(','))))
			# flag.set("hour", RTC().datetime()[4])
			# flag.set("minute", RTC().datetime()[5])
			# clear watchdog to skip ntp time sync
			time_synced.set()
			config.timesync_secs = time.time()
			debug("UTC: {}".format(j['UTC']) )

			if 'last_restart' not in versions:
				versions['last_restart'] = strftime()
				state.publish.set()

		if "timezone" in j and (config.timezone - 24) != j['timezone']:
				config.timezone = j['timezone'] + 24
				info("hass TIMEZONE: {}".format(config.timezone) )
		return

	if 'esp/{}'.format(espMAC) in td:
		client.set_last_will('hass/sensor/esp/{}/state'.format(espMAC), 'shutdown', retain=True)

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
	info("hass: mqtt_ping running")
	while True:
		try:
			await mqtt_connected.wait()
			client.ping()
			await asyncio.sleep(30)
		except asyncio.CancelledError:
			return
		except OSError:
			mqtt_connected.clear()
			mqtt_error.set()

# Check for incoming MQTT messages (calls callback if received)
async def check():
	info("hass: mqtt_check_msg running")
	while True:
		try:
			await mqtt_connected.wait()
			client.check_msg()
			await asyncio.sleep(0)
		except asyncio.CancelledError:
			return
		except OSError:
			mqtt_connected.clear()
			mqtt_error.set()

# Maintain MQTTclient connection, reconnect if flagged as bad
# TODO: "test" if server is available using sockets
async def mqtt():
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
			#state.attr = { "hostname": hostname, "versions": versions, "mac": espMAC, "ipv4": list(wlan.ifconfig())[0]}
			state.attr = versions
			client.connect(clean_session=True)
			client.ping()
			mqtt_connected.set()
			mqtt_error.clear()
			sub_all.set()
			state.set_state('online')
			state.publish.set()
			info("mqtt: connected: {}".format(config.mqtt_server) )
			await mqtt_error.wait()
		except asyncio.CancelledError:
			return
		except OSError:
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

start(mqtt)
start(ping)
start(check)
start(pub)
start(sub)

info("hass: core tasks created ..." )

