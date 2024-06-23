# ble.py

version = (2,0,10)
# 2 0 8: split scan to allow sleep(.1) to fix ctrl-c from netrepl
# 2 0 9: convert to bytes before putting into result for adv_data
# 2010: added exception checking in ble_loop

import bluetooth
import ubinascii
import time
from machine import reset
from alog import debug, info, error
import uasyncio as asyncio
from msgqueue import MsgQueue

_ISRESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IPCONN = const(7)
_IPDISC = const(8)
_IGSRESULT = const(9)
_IGCRESULT = const(11)
_IGCDONE = const(12)
_IGDRESULT = const(13)
_IGRRESULT = const(15)
_IGNOTIFY = const(18)
_IGIND = const(19)


ble_connect = MsgQueue(1)

# callback determines which queue based on oui search
result = MsgQueue(5)
# poll_result = MsgQueue(1)

# connection table for finding device in callback
# key = conn_handle, value = ble device object
conn_table = {}

# dicts to store incoming messages for devices of interest
polled_devices = {}
scanned_devices = {}

# Control scanning and polling (poll between scans)
ble_scan_done = asyncio.ThreadSafeFlag()

# device object for tracking state and updating via handles
class BleDevice:
	def __init__(self, mac, addr, device, rssi=0, conn_handle=None, 
			  	value_handle=None, uuid=None, write_value=None, 
				notify_data=None, connectable=None ):
		self.mac = mac
		self.addr = addr
		self.device = device
		self.rssi = rssi
		self.conn_handle = conn_handle
		self.value_handle = value_handle
		self.uuid = bluetooth.UUID(uuid) if uuid else None
		self.write_value = write_value
		self.notify_data = notify_data
		self.connected = asyncio.ThreadSafeFlag()
		self.received = asyncio.ThreadSafeFlag()
		self.disconnect = asyncio.ThreadSafeFlag()
		self.connectable = connectable
	
connect_error = asyncio.ThreadSafeFlag()

# WP6003 type polling device
def init_poll_for(device_class):
	polled_devices[device_class.oui] = device_class

# If too many errors when connecting to a device, do a hard reset on esp
async def gap_reset():
	last = time.time()
	count = 0
	while True:
		await connect_error.wait()
		count += 1
		error("gap_error: {}".format(count))
		if count < 30:
			# reset count if last error was a while ago
			if time.time() - last > 300:
				count = 0
			last = time.time()
			continue
		# reset if 30 errors within 5 minutes
		reset()
		while True:
			time.sleep(1)

#####################################
# General BLE callback handling Coros
#####################################

# Scan for 60 seconds, allow polling, repeat						
async def ble_loop():
	asyncio.create_task(handle_result())
	asyncio.create_task(handle_connect())
	while True:
		try:
			info("ble_loop: scanning 60 seconds in 6 intervals")
			for t in range(6):
				ble.gap_scan(10000,30000,30000,True)		
				await ble_scan_done.wait()
				time.sleep(.1)
			debug("ble_loop: polling cycle")
			for mac, bdevice in polled_devices.items():
				# Only poll devices, not signatures
				if hasattr(bdevice, 'mac'):
					await asyncio.gather(poll(bdevice) )
		except OSError:
			error("OSError during ble_loop")
		except:
			error("Unknown Error in ble_loop")

async def handle_result():
	global result
	async for mac, data in result:
		try:
			addr_type, addr, connectable, rssi, bdata = data
			# bdata = bytes(adv_data)
			oui = mac[0:6]
			#debug("handle_result: received")
			
			# add to scanned or polled if oui matches
			if mac not in scanned_devices and mac not in polled_devices:
				if oui in scanned_devices:
					error("adding scanned mac {}".format(mac) )
					new_device = scanned_devices[oui](mac)
					scanned_devices[mac] = BleDevice(mac,
											addr, 
											new_device, 
											rssi=rssi,
											connectable=connectable)

				if oui in polled_devices:
					error("adding polled mac: {}".format(mac ) )
					dc = polled_devices[oui]
					new_device = dc(mac)
					polled_devices[mac] = BleDevice(mac,
											addr,
											new_device, 
											rssi=rssi,
											write_value=dc.write_value,
											uuid=dc.uuid,
											connectable=connectable)

			# If scanned data, call update for that device
			if mac in scanned_devices:
				#debug("updating scanned mac: {}".format(mac ) )
				scanned_devices[mac].device.update(bdata)
			
		except Exception as e:
			error("handle_result: Caught exception")
			error(e)

async def handle_connect():
	global ble_connect
	async for mac, data in ble_connect:
		try:
			conn_handle, addr_type, addr = data
			debug("handle_connect: mac={}, connhandle={}, addr_t={}, addr={}".format(mac, conn_handle, addr_type,
								ubinascii.hexlify(bytes(addr)).decode()) )
			# set conn_handle
			polled_devices[mac].conn_handle = conn_handle
			# add to table for later lookup
			conn_table[str(conn_handle)] = polled_devices[mac]
			polled_devices[mac].connected.set()
		except Exception as e:
			error("handle_connect: Caught exception")
			error(e)

# govee device_class example is Govee5074
def init_scan_for(device_class):
	# oui added to scanned devices with Class to instantiate a device
	# callback uses this to add new devices to scanned_devices
	scanned_devices[device_class.oui] = device_class
	
def updatedevice(self, handle, value_handle=None, notify_data=None ):
	for mac, device in self.devices.items():
		if device.conn_handle == handle:
			if value_handle is not None:
				device.value_handle = value_handle
			if notify_data is not None:
				device.notify_data = notify_data
			device.waiting = False

def callback(event, data):
	global ble_connect
	global result
	# Maintain list of devices and queue data received

	if event == _ISRESULT:
		addr_type, addr, connectable, rssi, adv_data = data
		mac = ubinascii.hexlify(bytes(addr)).decode()
		result.put(mac, (addr_type, bytes(addr), connectable, rssi, bytes(adv_data)))
		#debug("cb: ISRESULT: mac {}".format(mac))		

	elif event == _IPCONN:
		conn_handle, addr_type, addr = data
		mac = ubinascii.hexlify(bytes(addr)).decode()
		ble_connect.put(mac, (conn_handle, addr_type, addr) )
		debug("cb: IPCONN: mac {}".format(mac))

	elif event == _IRQ_SCAN_DONE:
		ble_scan_done.set()
		debug("cb: IRQ_SCAN_DONE")

	elif event == _IPDISC:
		# Connected peripheral has disconnected.
		conn_handle, addr_type, addr = data
		mac = ubinascii.hexlify(bytes(addr)).decode()
		debug("cb: IPDISC: mac {}, addr {}".format(mac, bytes(addr) ) )
		if mac in polled_devices:
			polled_devices[mac].disconnect.set()
		debug("cb: IPDISC: mac {}".format(mac))

	elif event == _IGSRESULT:
		# Called for each service found by gattc_discover_services().
		conn_handle, start_handle, end_handle, uuid = data
		debug("ble cb: service found: {}, {}, {}, {}".format(conn_handle, start_handle, end_handle, uuid) )

	elif event == _IGCRESULT:
		# Called for each characteristic found by gattc_discover_services().
		conn_handle, def_handle, value_handle, properties, uuid = data
		debug("ble cb: char_result:{}, {}, {}, {}, {}".format(conn_handle, def_handle, value_handle, properties, uuid) )
		bdevice = conn_table[str(conn_handle)]
		bdevice.value_handle = value_handle
		bdevice.received.set()

	elif event == _IGDRESULT:
		# Called for each descriptor found by gattc_discover_descriptors().
		conn_handle, dsc_handle, uuid = data
		debug("ble cb: scanned descriptors: {}, {}, {}".format(conn_handle, dsc_handle, uuid) )
	elif event == _IGRRESULT:
		# A gattc_read() has completed.
		conn_handle, value_handle, char_data = data
		debug("ble cb: gattc read result: {}, {}, {}".format(conn_handle, value_handle, char_data) )
	elif event == _IGNOTIFY:
		# A peripheral has sent a notify request.
		conn_handle, value_handle, notify_data = data
		debug("ble cb: gattc notify: {}, {}, {}".format(conn_handle, value_handle, notify_data) )

		bdevice = conn_table[str(conn_handle)]
		bdevice.notify_data = notify_data
		bdevice.received.set()
		
	elif event == _IGIND:
		# A peripheral has sent an indicate request.
		conn_handle, value_handle, notify_data = data
		debug("ble cb: gattc indicate: {}, {}, {}".format(conn_handle, value_handle, notify_data) )
	elif event == _IGCDONE:
		# conn_handle, value_handle, notify_data = data
		debug("ble cb: gattc indicate: {}".format(data) )
	else:
		info("ble:cb: unknown event#: {}".format(event))

# use create_task to poll ble device using this Coro
async def poll(bdevice):
	try:
		# Send connect (step 1)
		bdevice.conn_handle = None
		bdevice.value_handle = None
		bdevice.connected = asyncio.ThreadSafeFlag()
		bdevice.disconnect = asyncio.ThreadSafeFlag()
		
		bdevice.received = asyncio.ThreadSafeFlag()
		time.sleep(1)
		info("poll: connecting to: mac: {}, addr: {}".format( bdevice.mac, bytes(bdevice.addr) ) )
		ble.gap_connect(0, bdevice.addr, 2000)

		# wait for 10 seconds for reply
		# when connected, conn_table and conn_handle are set
		# in handle_connect Coro
		await asyncio.wait_for(bdevice.connected.wait(), 5)
	
		# connected, send discover (step 2)
		debug("poll: sending discover characteristic {} to: {}".format(ubinascii.hexlify(bdevice.uuid), bdevice.mac) )
		bdevice.received = asyncio.ThreadSafeFlag()
		ble.gattc_discover_characteristics(bdevice.conn_handle, 1, 65535, bdevice.uuid)
		# wait 10 seconds for service
		await asyncio.wait_for(bdevice.received.wait(), 5)
				
		# found service, send write command to query
		debug("poll: sending write conn_handle = {}\n value_handle = {}\n write_value {}\n type {}".format(bdevice.conn_handle, bdevice.value_handle, bdevice.write_value, type(bdevice.write_value) ) )
		bdevice.received = asyncio.ThreadSafeFlag()
		ble.gattc_write(bdevice.conn_handle, bdevice.value_handle, bytes([bdevice.write_value]))
		debug("After gattc_write")
		# wait 10 seconds for service
		await asyncio.wait_for(bdevice.received.wait(), 5)

		# If data received, send to eventbus and remove from device instance
		info("poll: updating data for: {}".format(bdevice.mac) )
		bdevice.device.update(bdevice.notify_data)
		
		debug("poll: disconnecting device: {}".format(bdevice.mac) )
		conn_table.pop(str(bdevice.conn_handle) )
		ble.gap_disconnect(bdevice.conn_handle)
		# wait 10 seconds for disconnect
		await asyncio.wait_for(bdevice.disconnect.wait(), 5)
		debug("poll: disconnected: {}".format(bdevice.mac) )
			
	except asyncio.TimeoutError:
		error("poll: timeout polling device: {}".format(bdevice.mac) )

	except OSError:
		connect_error.set()
	
	except:
		error("poll: other polling error mac: {}".format(bdevice.mac) )
		
	if bdevice.conn_handle:
		conn_table.pop(str(bdevice.conn_handle) )

ble = bluetooth.BLE()
ble.active(True)
ble.irq(callback)
