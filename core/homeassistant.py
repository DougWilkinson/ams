# homeassistant.py

from versions import versions
versions[__name__] = 16
# 10: refactored version with Device changes
# 11: fixed attrs and versions to set last_restart immediately
# 12: moved timezone update for config and localtime to utc handler
# 13: added await_subscribe to wait for wifi and mqtt to connect
# 14: fixed missing binary_sensor in check for HA config
# 15: moved device.configured check to only ha config a device if dtype is right and not already set to True (light_bri and light_rgb)
# 16: renamed to homeassistant.py and split mqttserver to separate file

import asyncio
import time
from machine import RTC

from logger import info, error, debug
from system import config, start
from localtime import offset_time

from events import wifi_connected, time_synced, mqtt_connected
from events import mqtt_error, subscribe_all, device_added

import json

from device import Device, device_list
from events import config_changed
from mqttserver import MQTT

haconfig_topic = config.ha_config + "/{}/{}/config"
topic__template = config.ha_topic + "/{}/{}"

# setup MQTT client/handler - all configuration is done through profile settings
mqtt = MQTT()

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

		mqtt.publish(pub_topic + "/state", device.state.lower() if device.set_lower else device.state)

		if hasattr(device, 'attrs'):
			mqtt.publish(pub_topic + "/attrs", json.dumps(device.attrs) )

		device.needs_publishing.clear()

# Create HA entity based on dtype, publisher_task and subscribe if needed
async def device_handler():
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
				
				# subscribe now
				asyncio.create_task(mqtt.await_subscribe(device, topic) )

			if device.configured:
				continue

			# Create publisher task only if publish is True
			if device.publish:
				asyncio.create_task(publish_state(device))

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

			# Publish HA config message
			mqtt.publish(haconfig_topic.format(device.dtype, device.name ), json.dumps(msg) )

			device.configured = True
			
utc = Device('hass/utc', "unknown", dtype="mqtt", publish=False)

async def utc_handler():
	info("hass: utc_handler running")
	while True:
		async for _, utc_state in utc.q:
			try:
				j = json.loads(utc_state)
				
				if 'UTC' in j:
					RTC().datetime(tuple(int(i) for i in tuple(j['UTC'].split(','))))
					time_synced.set()
					config.timesync_secs = time.time()

				if "timezone" in j and (config.timezone - 24) != j['timezone']:
						config.timezone = j['timezone'] + 24
						offset_time(config.timezone)
						config_changed.set()
						config.save()
						debug("timezone updated: {}".format(config.timezone) )
			except:
				error('handle_utc: Error processing utc: {}'.format(utc_state))

start(utc_handler)
start(device_handler)

