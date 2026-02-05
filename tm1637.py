# tm1637.py

from versions import versions
versions[__name__] = 5
# 5: converted to new standard (no hass_setup)

from time import sleep_us
from machine import Pin
from system import start
from logger import info, error
from localtime import offset_time
from device import Device
import asyncio
from light import Light

CMD1 = const(64)
CMD2 = const(192)
CMD3 = const(128)
DSP_ON = const(8)
DELAY = const(10)
MSB = const(128)

_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B\x00\x40\x63')

defaults = {"pd_sck": 14,
			"dout": 12,
			"update_sec": 1,
			"k": 229
			}

class TM1637(Light):
	def __init__(self, name, data_pin=0, clock_pin=4, brightness="2", clock=True, display_string="", speed="180" ):
		super().__init__(name, state="ON", brightness=brightness)

		info(f'tm1637:{name}, data_pin={data_pin}, clock_pin={clock_pin}, state={self.state.state}, brightness={brightness}, speed={speed}')

		self.dio = Pin(data_pin, Pin.OUT, value=0)
		self.clk = Pin(clock_pin, Pin.OUT, value=0)
		sleep_us(DELAY)

		self.tm_brightness(brightness)

		# self._write_data_cmd()
		# self._write_dsp_ctrl()

		self.string = Device(name + "/string", display_string, dtype="sensor")
		# self.brightness = Device(name + "/brightness", brightness, dtype="sensor", notifier_setup=ha_setup)
		
		self.clock = clock

		# self.string = Device("string", "hello -- ")
		# self.brightness = Device("brightness", brightness)

		self.speed = Device("speed", speed)
		self.colon = False
		asyncio.create_task(self._display())
		if self.clock:
			asyncio.create_task(self.display_clock())
		asyncio.create_task(self._string(self.string.q) )

	def set_state(self, state):
		info("tm1637: set_state: {}".format(state))
		if state == "ON":
			self.tm_brightness(self.s_bri.state)
		else:
			self.tm_brightness("0")

	def set_brightness(self, brightness):
		info("tm1637: set_brightness: {}".format(brightness))
		self.tm_brightness(brightness)

	async def _string(self, queue):
		async for _ , msg in queue:
			if len(msg) > 0 and msg[0] == ":":
				self.string.state = msg[1:]
				self.colon = True

	async def display_clock(self):
		while True:
			try:
				if self.clock:
					str_time = "{: >2}{:0>2}".format(offset_time()[3], offset_time()[4])
					self.colon = True
					self.show(str_time)
					await asyncio.sleep(.5)
					self.colon = False
					self.show(str_time)
				await asyncio.sleep(.5)
			except:
				error('tm1637: error')

	async def _display(self):
		start = 0
		last = ""
		while True:
			try:
				await asyncio.sleep_ms(int(self.speed.state))

				# If string changes, reset start
				if self.string.event.is_set():
					self.string.event.clear()
					start = 0

				# wait for event if blank
				if self.string.state == "":
					self.show(self.string.state)
					self.string.event.clear()
					await self.string.event.wait()
					continue

				# display long string (scroll)
				if len(self.string.state) > 4:
					seg = ""
					digit = start
					for i in range(4):
						seg += self.string.state[digit]
						digit = (digit + 1) % len(self.string.state)
					start += 1
					if start == len(self.string.state):
						start = 0
					self.show(seg)
					# print(seg, end="\r")
					continue

				# display just string
				self.show(("    " + self.string.state)[-4:])
				self.string.event.clear()
				await self.string.event.wait()
				continue

			except asyncio.CancelledError:
				error("tm1637: cancelled: {}".format(self.name) )
				return
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

	def tm_brightness(self, val=None):
		
		# val is between 0 and 255 from light.py
		try:
			self._bright = int(7 * int(val) / 255)
			self._write_data_cmd()
			self._write_dsp_ctrl()
			info("tm1637: tm_brightness set: {}".format(self._bright))
		except:
			error('tm1637: error setting brightness')
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

	def encode_string(self, string, usecase=False):
		segments = bytearray(len(string))
		for i in range(len(string)):
			segments[i] = self.encode_char(string[i], usecase)
		return segments

	def encode_char(self, char, usecase=False):
		o = ord(char)
		if o == 32:
			return _SEGMENTS[36] # space
		if o == 42:
			return _SEGMENTS[38] # star/degrees
		if o == 45:
			return _SEGMENTS[37] # dash
		if o >= 97 and o <= 122:
			return _SEGMENTS[o-87] # lowercase a-z
		if o >= 48 and o <= 57:
			return _SEGMENTS[o-48] # 0-9
		error("Character out of range: {:d} '{:s}'".format(o, chr(o)))

	def show(self, string):
		segments = self.encode_string(string, False)
		if len(segments) > 1 and self.colon:
			segments[1] |= 128
		self.write(segments[:4])
