

from time import sleep_us
from machine import Pin
from core import error, started, offset_time
import asyncio

CMD1 = const(64)
CMD2 = const(192)
CMD3 = const(128)
DSP_ON = const(8)
DELAY = const(10)
MSB = const(128)

_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B\x00\x40\x63')

class TMClock:
	def __init__(self, data_pin=0, clock_pin=4, brightness=5):
		self.dio = Pin(data_pin, Pin.OUT, value=0)
		self.clk = Pin(clock_pin, Pin.OUT, value=0)
		sleep_us(DELAY)

		self._bright = brightness
		self._write_data_cmd()
		self._write_dsp_ctrl()

		asyncio.create_task(self._display())
					
	async def _display(self):
		started('TMClock')
		while True:
			try:
				str_time = "{: >2}{:0>2}".format(offset_time()[3], offset_time()[4])
				self.show(str_time)
				await asyncio.sleep(.5)
				self.show(str_time, colon=True)
				await asyncio.sleep(.5)
			except:
				error('tm1637: error')

	def _start(self):
		self.dio(0)
		sleep_us(DELAY)
		self.clk(0)
		sleep_us(DELAY)

	def _stop(self):
		self.dio(0)
		sleep_us(DELAY)
		self.clk(1)
		sleep_us(DELAY)
		self.dio(1)

	def _write_data_cmd(self):
		self._start()
		self._write_byte(CMD1)
		self._stop()

	def _write_dsp_ctrl(self):
		self._start()
		self._write_byte(CMD3 | DSP_ON | self._bright)
		self._stop()

	def _write_byte(self, b):
		for i in range(8):
			self.dio((b >> i) & 1)
			sleep_us(DELAY)
			self.clk(1)
			sleep_us(DELAY)
			self.clk(0)
			sleep_us(DELAY)
		self.clk(0)
		sleep_us(DELAY)
		self.clk(1)
		sleep_us(DELAY)
		self.clk(0)
		sleep_us(DELAY)

	def write(self, segments, pos=0):
		if not 0 <= pos <= 5:
			return
		self._write_data_cmd()
		self._start()

		self._write_byte(CMD2 | pos)
		for seg in segments:
			self._write_byte(seg)
		self._stop()
		self._write_dsp_ctrl()

	def encode_string(self, string):
		segments = bytearray(len(string))
		for i in range(len(string)):
			segments[i] = self.encode_char(string[i])
		return segments

	def encode_char(self, char):
		o = ord(char)
		if o == 32:
			return _SEGMENTS[36] # space
		if o >= 48 and o <= 57:
			return _SEGMENTS[o-48] # 0-9
		return _SEGMENTS[37] # dash
	
	def show(self, string, colon=False):
		segments = self.encode_string(string)
		if colon:
			segments[1] |= 128
		self.write(segments[:4])
