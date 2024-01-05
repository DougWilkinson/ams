# main.py

version = ( 1, 0, 0)

from network import WLAN, AP_IF, STA_IF
WLAN(AP_IF).active(False)
wlan = WLAN(STA_IF)
wlan.active(True)

import mysecrets
import asyncio
from gc import mem_free, collect
from aconfig import shutdown, load_config, save_json, tasks, pbus, pbus_todo, events, eventbus
from time import localtime, time, sleep
from machine import RTC, reset
import ntptime
from alog import espMAC, info, error, debug, started, stopped, exited, running
from umqtt.simple import MQTTClient

ntp_servers = ('192.168.5.1', ntptime.host)

# Taken from Peter Hinch's mqtt_as code
class MsgQueue:
    def __init__(self, size):
        self._q = [0 for _ in range(max(size, 4))]
        self._size = size
        self._wi = 0
        self._ri = 0
        self._evt = asyncio.Event()
        self.discards = 0

    def put(self, *v):
        self._q[self._wi] = v
        self._evt.set()
        self._wi = (self._wi + 1) % self._size
        if self._wi == self._ri:  # Would indicate empty
            self._ri = (self._ri + 1) % self._size  # Discard a message
            self.discards += 1

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._ri == self._wi:  # Empty
            self._evt.clear()
            await self._evt.wait()
        r = self._q[self._ri]
        self._ri = (self._ri + 1) % self._size
        return r

queue = MsgQueue(3)

client = MQTTClient(espMAC, mysecrets.mqtt_server,
	user=mysecrets.mqtt_user,
	password=mysecrets.mqtt_pass,
	keepalive=60)

config_loaded = asyncio.Event()		# config loaded and ready to connect
wifi_connected = asyncio.Event()
mqtt_connected = asyncio.Event()
mqtt_error = asyncio.Event()		# set by pub/sub if error to trigger reconnect
mqtt_puball = asyncio.Event()

# TODO: Add support for MQTT to update?
# TODO: make more robust, can fail for a long time without hard reset
async def rtclock(pid):
	started(pid)
	while True:
		try:
			for host in ntp_servers:
				try:
					ntptime.host = host
					ntptime.settime()
					info("rtclock: ntp time set from {}".format(host) )
					break
				except OSError:
					error("rtclock: error querying: {}".format(host))
		except asyncio.CancelledError:
			stopped(pid)
			return
		await asyncio.sleep(60)
	exited(pid)

# Subscribes and resubs when mqtt connection is lost
async def subscriber(pid):  # (re)connection.
	started(pid)
	while True:
		try:
			await wifi_connected.wait()
			await mqtt_connected.wait()
			await mqtt_puball.wait()
			await config_loaded.wait()
			for topic in tasks:
				if '/' in topic:
					debug('subscriber: {}'.format(topic) )
					client.subscribe(topic)
			debug("subscriber: All topics resubscribed")
			mqtt_puball.clear()
		except asyncio.CancelledError:
			stopped(pid)
			return
		except:
			# Signal mqtt connect handler to reconnect
			mqtt_connected.clear()
			mqtt_error.set()
	exited(pid)

# TODO: pubstate (aconfig) only lets one msg at a time, allow queue? Memory constraints?
async def publisher(pid):
	started(pid)
	while True:
		try:
			await pbus_todo.wait()
			await wifi_connected.wait()
			await mqtt_connected.wait()
			for topic, msg in pbus.items():
				client.publish(topic, msg, retain=True)
				debug("publisher: topic {}".format(topic) )
			pbus.clear()
			pbus_todo.clear()
		except asyncio.CancelledError:
			stopped(pid)
			return
		except:
			mqtt_connected.clear()
			mqtt_error.set()
			error('pub: Error during {}'.format(topic))
			await asyncio.sleep(1)
	exited(pid)

# Takes msgs out of queue (mqtt callback adds to queue)
# and adds to eventbus for tasks to handle
async def messages(pid):
	started(pid)
	while True:
		try:
			async for topic, msg in queue:
				debug("messages: rcvd: {}".format(topic) )
				if b'/shutdown/' in topic:
					error("messages: Shutdown in {} seconds".format(msg))
					await asyncio.sleep(int(msg))
					shutdown.set()
					break
				eventbus[topic.decode()] = msg.decode()
				# signal task that eventbus has a message for it
				events[topic.decode()].set()
		except asyncio.CancelledError:
			stopped(pid)
			return
	exited(pid)

# Keeps wifi connected, sets events to help other coros decide when to process
# TODO: Add error handling to do hard reset if WLAN gets wonky
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

# Callback for MQTTClient to put received msgs into queue (handled by messages() coro)
def msg_cb(topic, msg):
	queue.put(topic, msg)

# ping mqtt every 30 seconds and flag mqtt to reconnect if trouble
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
# TODO: Add code to "test" if server is available using sockets to
# 		avoid hanging when connecting. many clocks/lights can still run without mqtt

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
			mqtt_puball.set()
			await mqtt_error.wait()
		except asyncio.CancelledError:
			return
		except OSError:
			error("mqtt: connect error")
			await asyncio.sleep(2)
	exited(pid)

# Main coro that starts all other tasks (core) and (sensors)
# All coros are kept track in "tasks" for later cancel/stop
# TODO: How much memory is used to store this? Not needed?

async def main(pid):
	started(pid)
	tasks[pid] = asyncio.current_task()
	try:
		# Load core modules
		for _pid, coro in core.items():
			tasks[_pid] = asyncio.create_task(coro(_pid))

		collect()
		error("{}: awaiting core modules".format(mem_free()) )
		await asyncio.sleep(5)

		collect()
		n=time()
		error("{}: Starting sensor modules".format(mem_free()) )
		for sensor, settings in load_config("").items():
			filename = settings.get("module", None)
			if filename:
				collect()
				info("{}: loading {}".format(mem_free(), filename))
				im = __import__(filename)
				im.Class(sensor, settings)
				while len(pbus) > 0:
					await asyncio.sleep(1)
		running(pid)
		config_loaded.set()
		await shutdown.wait()
	except asyncio.CancelledError:
		stopped(pid)
		return
	
	exited(pid)

# Fancy shutdown of all tasks/coros by sending "cancel" and waiting a bit
# TODO: Not sure this is necessary and could be removed to save memory
# Helpful for restarting without a reboot?
# TODO: Find a better way to clear out the main Loop, could not find a reliable way to reset
# TODO: Some coros do not catch "cancel" exception and "hang". Need to understand this.	
async def shutdown_wait():
	if not shutdown.is_set():
		queue.put(b'/shutdown/', b'4')
	error("stopping tasks ...")
	for pid, task in tasks.items():
		info("stopping: {} - ".format(pid), end="")
		for t in range(20):
			if task.done():
				break
			task.cancel()
			await asyncio.sleep_ms(250)
		else:
			debug(' hung!')

# List of core "coros" to load in main()
# TODO: Could use this in a list to start all at once without tracking them to save mem

core = {
		'wifi': wifi,
		'mqtt_connection': mqtt_connection,
		'mqtt_ping': mqtt_ping,
		'mqtt_check': mqtt_check,  
		'messages': messages, 
		'rtclock': rtclock, 
		'publisher': publisher,
		'subscriber': subscriber }

# Clear previous values to allow a fresh restart if not doing a reset()
# Run main() coro from here and check for Ctrl-C

def start():
	tasks.clear()
	events.clear()
	eventbus.clear()
	pbus_todo.clear()
	pbus.clear()
	shutdown.clear()
	# print("shutdown obj: ", shutdown)
	try:
		print("starting main coro")
		asyncio.run(main("main"))
	except KeyboardInterrupt:
		error("\nBreak!")
	
	asyncio.run(shutdown_wait())

start()

