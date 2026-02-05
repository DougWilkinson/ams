# mqttserver.py

# manage connections to mqtt server
# split off from hass.py

from versions import versions
versions[__name__] = 11
# 10: split off from hass.py and turned into a class
# 11: fixed esp state - trigger update after reconnect to mqttserver

import asyncio
import time

from logger import info, error, debug
from profiles import espMAC
from system import config, start
from logger import strftime
import socket

from events import wifi_connected, mqtt_connected, mqtt_error, subscribe_all, config_changed

from umqtt.simple import MQTTClient
import json

from msgqueue import MsgQueue
from device import Device, device_list
from logger import strftime

versions["last_restart"] = strftime()

publish_queue = MsgQueue(50)

class MQTT:
	def __init__(self):

		self.client = None
		self.esp = Device('esp/{}'.format(espMAC), "online", needs_publishing=True)
		
		self.esp.attrs = versions

		# place for all subscribed topics and related device objects
		self.subscribed_topics = {}
	
		start(self.mqtt_connection_handler)
		start(self.ping_handler)
		start(self.check_msg_handler)
		start(self.publish_handler)
		start(self.subscribe_all_handler)

		info("mqtt: setup complete" )

	async def await_subscribe(self, device, topic):
		if topic not in self.subscribed_topics:
			self.subscribed_topics[topic] = device
		await wifi_connected.wait()
		await mqtt_connected.wait()
		self.subscribe_topic(topic)
								
	def subscribe_topic(self, topic):
		try:
			self.client.subscribe(topic)
			info('mqtt: subscribed: {}'.format(topic) )
		except:
			error('mqtt: subscribe failed: {}'.format(topic) )
			mqtt_error.set()

# Subscribes and resubs when mqtt connection is lost
	async def subscribe_all_handler(self):

		info("mqtt: subscribe_all_handler running")

		while True:
			try:
				await subscribe_all.wait()
				info("mqtt: sub_all: resubscribe pending wifi/mqtt reconnect")
				await wifi_connected.wait()
				await mqtt_connected.wait()
				
				# should be done as part of the devices
				# client.subscribe('hass/utc')

				for topic in self.subscribed_topics:
					self.subscribe_topic(topic)
									
				info("mqtt: sub_all: resubscribe scheduled all devices")
				
				subscribe_all.clear()

			except Exception as e:
				error("mqtt: ping: {}".format(e) )
				# Signal mqtt reconnect
				mqtt_connected.clear()
				mqtt_error.set()

	def publish(self, topic, msg):
		publish_queue.put((topic, msg))

	async def publish_handler(self):
		global publish_queue

		info("mqtt: publish_handler running")

		while True:
			async for pubitem in publish_queue:
				try:
					topic, msg = pubitem
					debug("mqtt:pub: topic: {}".format(topic) )
					await wifi_connected.wait()
					await mqtt_connected.wait()
					self.client.publish(topic, msg, retain=True)
				
				except ValueError:
					error('mqtt:pub: ValueError unpacking {}'.format(pubitem))
				
				except Exception as e:
					error('mqtt:pub: Error handling topic {} - {}'.format(topic, e))
					mqtt_connected.clear()
					mqtt_error.set()
					await asyncio.sleep(1)

	# ping mqtt every 30 seconds
	async def ping_handler(self):
		info("mqtt: ping_handler running")
		while True:
			try:
				await mqtt_connected.wait()
				self.client.ping()
				await asyncio.sleep(30)
			except Exception as e:
				error("mqtt:ping_handler:error: {}".format(e) )
				mqtt_connected.clear()
				mqtt_error.set()

	# Check for incoming MQTT messages (calls callback if received)
	async def check_msg_handler(self):
		info("mqtt: check_msg_handler running")
		while True:
			try:
				await mqtt_connected.wait()
				self.client.check_msg()
				await asyncio.sleep(0)
			
			except Exception as e:
				error("mqtt:check_msg:error: {}".format(e) )
				mqtt_connected.clear()
				mqtt_error.set()


	# test if server is available using sockets before trying to connect
	def check_reachability(self, mqtt_server, mqtt_port) -> bool:
		sock = socket.socket()

		try:
			debug('mqtt:check_reachability: testing socket connection to {}'.format(mqtt_server) )

			# setblocking(False) or settimeout(0) does not work? ERRNO 119 ?
			sock.settimeout(1)

			sock.connect((mqtt_server, mqtt_port))

		except OSError as e:
			if e.args[0] == 116:
				error("mqtt:check_reachability: timed out" )
			else:
				error("mqtt:check_reachability: OSError: {} - reboot needed?".format(e) )
			sock.close()
			return False
			
		except:
			error("mqtt:check_reachability: Unknown error - reboot needed?" )
			return False

		sock.close()
		debug('mqtt:check_reachability: server {} appears online'.format(mqtt_server))
		return True

	async def esp_state_handler(self):
		for _, ev in self.esp_state.q:
			await wifi_connected.wait()
			await mqtt_connected.wait()
			if ev == 'shutdown':
				self.client.set_last_will('hass/sensor/esp/{}/state'.format(espMAC), 'shutdown', retain=True)
			else:
				self.client.publish('hass/sensor/esp/{}/state'.format(espMAC), ev, retain=True)

	# Callback for messages
	def msg_received_callback(self, topic, msg):
		#debug('cb: topic: {}'.format(topic))
		global state
		td = topic.decode("utf-8")

		if td in self.subscribed_topics:
			# get the device object to update it
			device = self.subscribed_topics[td]
			
			# update device state with new value
			device.set_state(msg.decode("utf-8"))

			# REMOVED TO SEE IF THIS NEEDS TO BE HERE - WHY PUBLISH STATE HERE?
			# EVERY DEVICE SHOULD HAVE A DEVICE HANDLER THAT SETS THE STATE
						
			# # put directly in publish_queue to be published on next await
			# if device.publish:
			# 	device.needs_publishing.clear()
			# 	publish_queue.put(gen_topic(device,"/state"), device.state.lower() if device.set_lower else device.state)

	# Maintain MQTTclient connection, reconnect if flagged as bad
	async def mqtt_connection_handler(self):
		info("mqtt: mqtt_connection_handler running")

		while True:
			try:
				info("mqtt:connect: waiting for wifi connection")
				await wifi_connected.wait()

				if not (config.mqtt_server and config.mqtt_username and config.mqtt_password):
					error("mqtt:connect: waiting for mqtt configuration")
					await config_changed.wait()
					continue

				if config.mqtt_ssl:
					client_port = 8883
					ssl_params = {'server_hostname': config.mqtt_server}
				else:
					client_port = 1883
					ssl_params = {}

				# use socket to test for mqtt port availability to avoid long timeouts
				if not self.check_reachability(config.mqtt_server, client_port):
					error("mqtt:connect: reachability test failed for {} - sleeping 30 seconds".format(config.mqtt_server) )
					await asyncio.sleep(30)
					continue

				info("mqtt:connect: Connecting to: {}".format(config.mqtt_server) )

				self.client = MQTTClient(espMAC, 
						config.mqtt_server, 
						port=client_port, 
						ssl=config.mqtt_ssl, 
						ssl_params=ssl_params, 
						user=config.mqtt_username, 
						password=config.mqtt_password,
						keepalive=60)

				self.client.set_callback(self.msg_received_callback)
				self.client.set_last_will('hass/sensor/esp/{}/state'.format(espMAC), 'offline', retain=True)

				self.client.connect(clean_session=True)
				
				self.client.ping()
				mqtt_connected.set()
				mqtt_error.clear()
				subscribe_all.set()
				self.esp.needs_publishing.set()

				info("mqtt:connect: connected to: {}".format(config.mqtt_server) )
				await mqtt_error.wait()

				error("mqtt:connect: connection error: {}".format(config.mqtt_server) )

			except Exception as e:
				error("mqtt:connect_handler: mqtt.client connect error: {}".format(e) )
				await asyncio.sleep(2)

