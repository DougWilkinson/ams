# gpsntp.py

from machine import UART, Pin, RTC
import time
import asyncio
import ntptime
from core import info, error, started

global last_pps
global current_pps    

rtc = RTC()

pps_event = asyncio.Event()

class GPS:
	def __init__(self):
		global pps_event
		self.uart = UART(2, 9600)
		self.pps = Pin(34, Pin.IN)
		self.last_pps = time.ticks_us()
		self.current_pps = self.last_pps
		self.ppi = self.pps.irq(trigger=Pin.IRQ_RISING, handler=self.pps_callback)
		self.samples = [1000000] * 10
		self.buffer = bytearray(100)
		self.time_ticks = 0
		self.rtc_us = 0
		#ntptime.settime()
		#error("ntptime set: {}".format(rtc.datetime() ) )
		
		# self.set_rtc_from_gps()

		asyncio.create_task(self.show_gps_diff())
		asyncio.create_task(self.set_rtc_from_gps())

	def pps_callback(self, pin):
		self.time_ticks = time.ticks_us()
		self.rtc_us = rtc.datetime()[7]
		pps_event.set()

	# $GPRMC,131706.00,A,4145.95092,N,07123.38417,W,0.158,,290325,,,A*6E\r\n
	# >>> r.datetime() (2025, 3, 29, 5, 15, 41, 53, 97550)
	# Year, month, day, day of week, hour, minute, second, microsecond    
	async def show_gps_diff(self):
		started("show_gps_diff")
		last_diff = 0
		while True:
			await pps_event.wait()
			current_rtc = list(rtc.datetime())
			if abs(time.ticks_us() - self.time_ticks - rtc.datetime()[7]) < 999999:
				if abs(time.ticks_us() - self.time_ticks - rtc.datetime()[7]) > 100:
					current_rtc[7] = time.ticks_us() - self.time_ticks
					rtc.datetime(tuple(current_rtc))
					error("rtc set: {}".format(current_rtc) )
				info("diff: {}".format(time.ticks_us() - self.time_ticks - rtc.datetime()[7] ) )
			else:
				error("diff discarded - too large")
			#info(self.get_gpmrc()[0:30] )
			pps_event.clear()

	def get_gpmrc(self):
		# clear buffer

		self.uart.read()
		
		#info("waiting for $GPRMC" )
		
		started = time.ticks_ms()

		buffer = ""	
		while time.ticks_ms() - started < 5000:
			# try:
			byte_line = self.uart.read()
			if byte_line:
				#print("byte_line: {}".format(byte_line) )
				try:
					buffer += byte_line.decode()
				except:
					buffer = ""
					self.uart.read()
					pass
			
			start = buffer.find("$GPRMC")

			if start >= 0:
				buffer = buffer[start:]
				if '\r\n' in buffer:
					buffer = buffer[:buffer.find("\r\n")]
					info("found in {} ms".format(time.ticks_ms() - started) )
					return buffer
			# except Exception as e:
			# 	error("Error: {}".format(e) )
			
	async def set_rtc_from_gps(self):
		started("set_rtc_from_gps")
		while True:
			nmea = self.get_gpmrc()
			nmea_time = nmea.split("$GPRMC,")[1]

			# ['233715.00', 'A', '5555.5444', 'N', '999.999', 'W', '0.415', '', '290325', '', '', 'A*66\r\n']
			nmea_date = nmea_time.split(",")[8]
		
			# set rtc datetime tuple, day of week and microseconds are ignored
			# day of week gets calculated even though 0 is specified

			rtc_tuple = rtc.datetime()
			datetime_tuple = (int(nmea_date[4:6]) + 2000, int(nmea_date[2:4]), int(nmea_date[0:2]), rtc_tuple[3], int(nmea_time[0:2]), int(nmea_time[2:4]), int(nmea_time[4:6]), rtc_tuple[7])
			if datetime_tuple != rtc_tuple:
				rtc.datetime(datetime_tuple)
				error("rtc set from gps: {}".format(datetime_tuple) )
			info("rtc: {}, gps: {}".format(rtc_tuple, datetime_tuple) )
			await asyncio.sleep(10)



