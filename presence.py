# presence.py

version = (2,0,0)

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
		self.human = UART(uart, baudrate=baudrate, tx=tx, rx=rx)
		#self.stream = asyncio.StreamReader(self.human)
		#self.writer = asyncio.StreamWriter(self.human)
		self.buffer = bytearray(512)
		self.last_reading = None
		self.motion = Device("{}_motion".format(name), "off", dtype="binary_sensor", notifier_setup=ha_setup )
		self.m_dist = Device("{}_motion_distance".format(name), state="0", units="m", notifier_setup=ha_setup )
		self.presence = Device("{}_presence".format(name), "off", dtype="binary_sensor", notifier_setup=ha_setup )
		self.p_dist = Device("{}_presence_distance".format(name), state="0", units="m", notifier_setup=ha_setup )
		self.ack = False
		
		# last values read for sensor
		self.status = 0
		self.m_distance = 0
		self.m_energy = 0
		self.p_distance = 0
		self.p_energy = 0
		self.det_dist = 0
		
		# self.timer = Timer(0)
		# self.timer.init(period=50,mode=Timer.PERIODIC, callback=self.callback)
		asyncio.create_task(self.read_sensor())

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
			print("bad length: ", len(self.last_reading))
			return False

		# update values
		self.status, self.m_distance, self.m_energy, self.s_distance, self.s_energy, self.det_dist = struct.unpack('<bhbhbh', self.last_reading)

		return True

	async def read_sensor(self):
		while True:
			if self.get_status():
				if self.status == 1:
					# update motion
					self.motion.set_state("on")
					self.m_dist.set_state(self.m_distance)
					info("Motion distance: {} cm ({})".format(m_distance, m_energy) )

				if self.status == 2:
					# update stationary
					self.motion.set_state("on")
					self.m_dist.set_state(self.p_dis)
					info("Stationary distance: {} cm ({})".format(s_distance, s_energy) )

				if self.status > 0:
					info("s: {}, md: {}, me: {}, sd: {}, se: {}, dd: {}".format(self.status, self.m_distance, self.m_energy, self.s_distance, self.s_energy, self.det_dist) )

			await asyncio.sleep_ms(100)

	def send_wait(self, command):
		debug("Sending: {}".format(command))		
		for i in range(3):
			self.human.read(self.human.any())
			self.human.write(CMD_START + command + CMD_END)
			sleep_ms(500)
			result = self.human.read()
			#print(result)
			if result and CMD_START in result:
				info(result)
				return result
		error("sendcmd: Ack timed out!")
		return None

	# def wait_for_ack(self):
	# 	for i in range(5):
	# 		debug("dc: any: {}".format(self.human.any() ) )
	# 		status = self.human.read(self.human.any())
	# 		self.buffer += status
	# 		debug("dc({}): {}".format(len(self.buffer), self.buffer[-30:]) )
		
	# 		if CMD_START in self.buffer and CMD_END in self.buffer:
	# 			start_index = self.buffer.index(CMD_START) + 4
	# 			end_index = self.buffer.index(CMD_END)
	# 			if start_index < end_index:
	# 				self.last_reading = self.buffer[start_index:end_index]
	# 				self.buffer = self.buffer[4 - end_index:]
	# 				debug("buffupd({}): {}".format(len(self.buffer), self.buffer[-30:]) )
	# 			else:
	# 				self.buffer = self.buffer[end_index+4:]
	# 				debug("buffclean({}): {}".format(len(self.buffer), self.buffer[-30:]) )
	# 			debug("Ack: ", self.last_reading)
	# 		sleep_ms(100)

	def watch(self):
		last = ""
		while True:
			if self.get_status():
				if last != self.last_reading:
					debug(self.last_reading)
					info("s: {}, md: {}, me: {}, sd: {}, se: {}, dd: {}".format(self.status, self.m_distance, self.m_energy, self.s_distance, self.s_energy, self.det_dist) )
					last = self.last_reading
			sleep_ms(10)

	def sendcmd(self, command, restart=False):
		#info("Config enable:")
		self.send_wait( CONFIG_START)

		info("command:")
		info(self.send_wait( command ) )
		
		if restart:
			info(self.send_wait(RESTART))
			info("\nRESTARTED SENSOR\n")
			return
		
		#info("Config disable:")
		self.send_wait( CONFIG_END )

	def read_params(self):
		self.sendcmd(READ_PARAMS)

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
		struct.unpack('<ihhhhi',result)

	def set_resolution(self, res):
		set_res_cmd = b'\x04\x00\xaa\x00' + struct.pack('<h', res)
		self.sendcmd(set_res_cmd, restart=True)
	
	def set_max_door(self, motion, resting):
		set_max_cmd = SET_MAX_DOOR + struct.pack('<hihihi', 0, motion, 1, resting, 2, 5)
		self.sendcmd(set_max_cmd, restart=True)
