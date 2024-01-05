# aconfig.py

version = (1, 0, 0)

import json
from haconfig import haconfig_topic, haconfig_msg
from alog import info, debug, error, espMAC
from gc import mem_free, collect
from micropython import mem_info
import asyncio

shutdown = asyncio.Event()			# shutdown signal for all coros
pbus_todo = asyncio.Event()			# set if publisher has work to do

pbus = {}		# publish bus
tasks = {}		# list of task names and task objs (may not be needed)
events = {}		# list of event names (mqtt topics) for setting event when received
eventbus = {}	# event messages stored here by event name

# define event and start task for "name"
# if name has "hass" already in it, use that name
# otherwise, wrap name to be "hass/<name>/set"
def addtask(name, handler):
	full = name
	if "hass/" not in name:
		full = "hass/{}/set".format(name)
	debug("addtask: {}".format(full))
	if full in tasks:
		debug("addtask: dup {}".format(full))
		return
	e = asyncio.Event()
	events[full] = e
	tasks[full] = asyncio.create_task(handler(e) )

# Add /state to name and add to pbus for publishing
# Add to local eventbus if defined
async def pubstate(name, msg, template="hass/{}/state"):
	topic = template.format(name)
	# Add to eventbus if local event defined
	if topic in events:
		eventbus[topic] = msg
		events[topic].set()
	while pbus_todo.is_set():
		await asyncio.sleep(0)
	topic = template.format(name)
	pbus[topic] = str(msg)
	# give loopback priority to duplicate events like motion -> ledlight back to eventbus
	# loopback sets this when done, publisher waits for this to be set
	# loopback_done.clear()
	# set to tell publisher items waiting to publish
	pbus_todo.set()
	#debug("pubstate: {}".format(topic) )

# Generate and publish json needed to create entities in HomeAssistant using autoconfig
# Uses haconfig.py for entity details
# Only publishes one at a time to avoid memory issues

async def publish_haconfig(entity, units):
	while pbus_todo.is_set():
		await asyncio.sleep(0)
	debug("publish_haconfig: {}\n{}".format(haconfig_topic.format(entity),haconfig_msg(entity, units) ) )
	pbus[haconfig_topic.format(entity)] = haconfig_msg(entity, units)
	pbus_todo.set()

# combines addtask and haconfig above into a single call
# Called from sensor modules (ie. binrary_sensor, lights, dht, etc)
def setup(name, handler, entity="", units=""):
	addtask(name, handler)
	if not entity:
		entity = name
	asyncio.create_task(publish_haconfig(entity, units))
	# asyncio.create_task(pubstate(name, "OFF"))

# Load a file from flash, default is the config file named with the MAC address
# load_config is redundant, if instance name is given, returns only that part of config
# This was done to save on memory and not load entire config which can be lengthy
		
def load_file(name=espMAC, instance=""):
	try:
		full = {}
		with open(name) as file:
			raw = file.readline()
			while raw:
				kv = json.loads(raw)
				if instance and instance in kv:
					return kv[instance]
				full.update(kv)
				raw = file.readline()
		return full
	except:
		error("load_file: {} failed.".format(name))
		return {}

def load_config(instance):
	return load_file(name=espMAC, instance=instance)

# redundant for save_file
def save_json(name, json_data) -> bool:
	return save_file(name, json_data)

# saves file in json format, separate lines to allow for reading partial config (above)
# TODO: combine with a setup script to allow configuration via web/AP mode?

def save_file(name, content) -> bool:
	try:
		with open(name, "w") as file:
			for k,v in content.items():
				file.write(json.dumps({k:v}) )
				file.write("\n")
		info('Saved config {}'.format(name))
		return True
	except:
		error('save_file: {} failed'.format(name))
		return False
