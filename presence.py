# presence.py

# radar 24GHz sensor (Seeed XIAO)
from versions import versions
versions[__name__] = 3

from machine import UART, Timer
import ubinascii
from time import time, sleep_ms
from core import debug, info, error, latch
import uasyncio as asyncio

from hass import ha_setup
from device import Device
import struct

#import asyncio
# from network import WLAN, AP_IF, STA_IF
# WLAN(AP_IF).active(False)
# WLAN(STA_IF).active(False)

FRAME_START = b'\xf4\xf3\xf2\xf1'
FRAME_END = b'\xf8\xf7\xf6\xf5'

CMD_START = b'\xfd\xfc\xfb\xfa'
CMD_END = b'\x04\x03\x02\x01'

CONFIG_START = b'\x04\x00\xff\x00\x01\x00'
CONFIG_END = b'\x02\x00\xfe\x00'

#COMMANDS
ENG_MODE = b'\x02\x00\x62\x00'
NORMAL_MODE = b'\x02\x00\x63\x00'

BTMAC = b'\x04\x00\xa5\x00\x01\x00'
RESTART = b'\x02\x00\xa3\x00'
VERSION = b'\x02\x00\xa0\x00'
READ_PARAMS = b'\x02\x00\x61\x00'
GET_RESOLUTION = b'\x02\x00\xab\x00'
SET_MAX_DOOR = b'\x14\x00\x60\x00'
	
# detector sends about 10 per second
class Presence:
	def __init__(self, name, uart=1, baudrate=256000, tx=2, rx=4 ):
		
		self.uart = uart
		self.baudrate = baudrate
		self.tx = tx
		self.rx = rx
		
		self.uart_init()

		self.buffer = bytearray(512)
		self.last_reading = None

		self.motion = Device("{}_motion".format(name), "OFF", dtype="binary_sensor", notifier_setup=ha_setup )
		self.m_distance = Device("{}_motion_distance".format(name), state="0", units="cm", notifier_setup=ha_setup )
		self.presence = Device("{}_presence".format(name), "OFF", dtype="binary_sensor", notifier_setup=ha_setup )
		self.p_distance = Device("{}_presence_distance".format(name), state="0", units="cm", notifier_setup=ha_setup )
		self.ack = False
		
		# last values read for sensor
		self.status = 0
		self.m_dist = 0
		self.m_energy = 0
		self.p_dist = 0
		self.p_energy = 0
		self.det_dist = 0

		self.m_door = Device("{}_motion_door".format(name), state="0", units="cm", notifier_setup=ha_setup )
		self.p_door = Device("{}_presence_door".format(name), state="0", units="cm", notifier_setup=ha_setup )
		self.get_resolution()
		self.read_params()

		asyncio.create_task(self.read_sensor())
		asyncio.create_task(self.update_door(self.m_door))
		asyncio.create_task(self.update_door(self.p_door))

	def uart_init(self):
		self.human = UART(self.uart, baudrate=self.baudrate, tx=self.tx, rx=self.rx)
		error("uart_init: uart={}, baudrate={}, tx={}, rx={}".format(self.uart, self.baudrate, self.tx, self.rx) )

	async def update_door(self, door):
		async for _, msg in door.q:
			# try:
			newval = int(msg)
			# if newval > 0 and newval < 9:
			# 	raise ValueError
			door.set_state(newval)
			self.set_max_door()
			info("{} new value: {}".format(door.name, msg))
			# except ValueError:
			# error("invalid door value: {}".format(msg))

	def get_status(self):
		status = self.human.read(self.human.any())
		self.buffer += status

		if FRAME_START not in self.buffer or FRAME_END not in self.buffer:
			return False
		#print("ds: {}".format(self.buffer) )
		start_index = self.buffer.index(FRAME_START) + 8
		end_index = self.buffer.index(FRAME_END)
		
		# remove bad data from buffer (min length check too)
		if start_index > end_index:
			# Remove garbage
			self.buffer = self.buffer[end_index+4:]
			return False
		
		# update device values
		self.last_reading = self.buffer[start_index:end_index]
		self.buffer = self.buffer[-4 - end_index:]
		if len(self.last_reading) < 11:
			error("bad status length: {}".format(len(self.last_reading) ) )
			return False

		# update values
		self.status, self.m_dist, self.m_energy, self.p_dist, self.p_energy, self.det_dist = struct.unpack('<BhBhBh', self.last_reading)
		
		if self.m_dist < 0 or self.m_dist > 500:
			return False
		if self.p_dist < 0 or self.p_dist > 500:
			return False
		
		return True

	async def read_sensor(self):
		last_status = -1
		while True:
			self.human.read()
			await asyncio.sleep_ms(100)
			if not self.get_status():
				continue
			
			if last_status != 0 and self.status == 0:
				# update no presence or motion
				self.motion.set_state("OFF")
				self.presence.set_state("OFF")
				self.m_distance.set_state(0)
				self.p_distance.set_state(0)

			if self.status & 1:
				# update motion
				self.motion.set_state("ON")
				if abs(self.m_dist - int(self.m_distance.state)) > 30:
					self.m_distance.set_state(self.m_dist)
					info("Motion distance: {} cm ({})".format(self.m_dist, self.m_energy) )

			if self.status & 2:
				# update stationary
				self.presence.set_state("ON")
				if abs(self.p_dist - int(self.p_distance.state)) > 30:
					self.p_distance.set_state(self.p_dist)
					info("Stationary distance: {} cm ({})".format(self.p_dist, self.p_energy) )

			# if self.status >:
			# 	error("s: {}, md: {}, me: {}, sd: {}, se: {}, dd: {}".format(self.status, self.m_dist, self.m_energy, self.p_dist, self.p_energy, self.det_dist) )
			# elif self.status > 0:
			# 	info("s: {}, md: {}, me: {}, sd: {}, se: {}, dd: {}".format(self.status, self.m_dist, self.m_energy, self.p_dist, self.p_energy, self.det_dist) )

			last_status = self.status

	# used only to send commands (not general status processing)
	def send_wait(self, command):
		#debug("Sending: {}".format(command))		
		for i in range(3):
			# clear buffer
			self.human.read(self.human.any())
			self.human.write(CMD_START + command + CMD_END)
			sleep_ms(500)
			result = self.human.read()
			#print(result)
			if result and CMD_START in result:
				#info(result)
				return result
			self.uart_init()
			sleep_ms(100)
		error("sendcmd: Ack timed out!")
		return None

	def watch(self):
		last = ""
		while True:
			if self.get_status():
				if last != self.last_reading:
					debug(self.last_reading)
					info("s: {}, md: {}, me: {}, sd: {}, se: {}, dd: {}".format(self.status, self.m_dist, self.m_energy, self.p_dist, self.p_energy, self.det_dist) )
					last = self.last_reading
			sleep_ms(10)

	def sendcmd(self, command, restart=False):
		#info("Config enable:")
		if not self.send_wait( CONFIG_START):
			error("Start config not confimed!")
			return None
		
		#info("command:")
		result = self.send_wait( command )
		if not result:
			return None
		
		if restart:
			if not self.send_wait(RESTART):
				error("restart failed!")
		
			info("RESTARTED SENSOR")
			return result
		
		#info("Config disable:")
		if not self.send_wait( CONFIG_END ):
			error("End config not confirmed!")

		return result

	def read_params(self):
		params = self.sendcmd(READ_PARAMS)
		self.m_door.set_state(params[12])
		self.p_door.set_state(params[13])
		info("Seeed XIAO: Max door: {}, Max motion door: {}, max pres. door:{}".format(params[11], self.m_door.state, self.p_door.state) )
	
	def eng_mode(self):
		self.sendcmd(ENG_MODE)

	def normal_mode(self):
		self.sendcmd(NORMAL_MODE)

	def btmac(self):
		self.sendcmd(BTMAC)

	def reset(self):
		self.sendcmd(RESTART)

	def version(self):
		self.sendcmd(VERSION)

	#                             ACK      Status   Value
	# b'\xfd\xfc\xfb\xfa \x06\x00 \xab\x01 \x00\x00 \x00\x00 \x04\x03\x02\x01'
	#                                      0=good   0=0.75m 1=0.2m
	def get_resolution(self):
		result = self.sendcmd(GET_RESOLUTION)
		if result:
			_ , _, _, resolution, _ , _ = struct.unpack('<ihhhhi',result)
			info("Seeed XIAO: Resolution = {}".format(resolution))

	def set_resolution(self, res):
		set_res_cmd = b'\x04\x00\xaa\x00' + struct.pack('<h', res)
		self.sendcmd(set_res_cmd, restart=True)
	
	def set_max_door(self):
		set_max_cmd = SET_MAX_DOOR + struct.pack('<hihihi', 0, int(self.m_door.state), 1, int(self.p_door.state), 2, 5)
		self.sendcmd(set_max_cmd, restart=True)
