#XPT2046.py
# Touch module on ili9341
# asyncio version

from core import started, info
from time import sleep, time
import asyncio
from device import Device
from hass import ha_setup

class Touch(object):
	"""Serial interface for XPT2046 Touch Screen Controller."""

	# Command constants from ILI9341 datasheet
	GET_X = const(0b11010000)  # X position
	GET_Y = const(0b10010000)  # Y position
	GET_Z1 = const(0b10110000)  # Z1 position
	GET_Z2 = const(0b11000000)  # Z2 position
	GET_TEMP0 = const(0b10000000)  # Temperature 0
	GET_TEMP1 = const(0b11110000)  # Temperature 1
	GET_BATTERY = const(0b10100000)  # Battery monitor
	GET_AUX = const(0b11100000)  # Auxiliary input to ADC

	def __init__(self, spi, cs=26, int_pin=None, int_handler=None,
				 width=240, height=320,
				 x_min=100, x_max=1962, y_min=100, y_max=1900):
		"""Initialize touch screen controller.
		Args:
			spi (Class Spi):  SPI interface for OLED
			cs (Class Pin):  Chip select pin
			int_pin (Class Pin):  Touch controller interrupt pin
			int_handler (function): Handler for screen interrupt
			width (int): Width of LCD screen
			height (int): Height of LCD screen
			x_min (int): Minimum x coordinate
			x_max (int): Maximum x coordinate
			y_min (int): Minimum Y coordinate
			y_max (int): Maximum Y coordinate
		"""
		self.spi = spi
		self.cs = cs
		self.cs.init(self.cs.OUT, value=1)
		self.rx_buf = bytearray(3)  # Receive buffer
		self.tx_buf = bytearray(3)  # Transmit buffer
		self.width = width
		self.height = height
		# Set calibration
		self.x_min = x_min
		self.x_max = x_max
		self.y_min = y_min
		self.y_max = y_max
		self.x_multiplier = width / (x_max - x_min)
		self.x_add = x_min * -self.x_multiplier
		self.y_multiplier = height / (y_max - y_min)
		self.y_add = y_min * -self.y_multiplier
		
		asyncio.create_task(self.get_touch())

		if int_pin is not None:
			self.int_pin = int_pin
			self.int_pin.init(int_pin.IN)
			self.int_handler = int_handler
			self.int_locked = False
			self.int_pin.irq(trigger=int_pin.IRQ_FALLING | int_pin.IRQ_RISING,
						handler=self.int_press)

	async def get_touch(self):
		started("Touch")
		last_touch = time()
		touch = Device("touch", "0,0", dtype="sensor", ro=True, publish=False, notifier_setup=ha_setup)		
		while True:
			# get a new value
			sample = self.raw_touch()  # get a touch
			if sample is None:
				if touch.state != "0,0" and (time() - last_touch > 1):
					touch.set_state("0,0")
			else:
				info(sample)
				touch.set_state("{},{}".format(*sample) )
				last_touch = time()
			await asyncio.sleep(0)
		return None

	def int_press(self, pin):
		"""Send X,Y values to passed interrupt handler."""
		if not pin.value() and not self.int_locked:
			self.int_locked = True  # Lock Interrupt
			buff = self.raw_touch()

			if buff is not None:
				x, y = self.normalize(*buff)
				self.int_handler(x, y)
			sleep(.1)  # Debounce falling edge
		elif pin.value() and self.int_locked:
			sleep(.1)  # Debounce rising edge
			self.int_locked = False  # Unlock interrupt

	def normalize(self, x, y):
		"""Normalize mean X,Y values to match LCD screen."""
		x = int(self.x_multiplier * x + self.x_add)
		y = int(self.y_multiplier * y + self.y_add)
		return x, y

	def raw_touch(self):
		"""Read raw X,Y touch values.
		Returns:
			tuple(int, int): X, Y
		"""
		x = self.send_command(self.GET_X)
		y = self.send_command(self.GET_Y)
		if self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max:
			return (x, y)
		else:
			return None

	def send_command(self, command):
		"""Write command to XT2046 (MicroPython).
		Args:
			command (byte): XT2046 command code.
		Returns:
			int: 12 bit response
		"""
		self.tx_buf[0] = command
		self.cs(0)
		self.spi.write_readinto(self.tx_buf, self.rx_buf)
		self.cs(1)

		return (self.rx_buf[1] << 4) | (self.rx_buf[2] >> 4)

