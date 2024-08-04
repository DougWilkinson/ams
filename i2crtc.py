# i2crtc.py

#### wifi RTC over i2c
from machine import Pin, RTC, SoftI2C
import uasyncio as asyncio
#from i2cs import I2CS

# set to start listening i2c channel by irq callback
incoming = asyncio.Event()

class I2CRTC:
	def __init__(self, scl=0, sda=2) -> None:
		self.i2cs = SoftI2C(scl=Pin(scl), sda=Pin(sda))
		# self.sda.irq(trigger=Pin.IRQ_FALLING, handler=self.callback)

	def wait_for_cmd(self):
		print("Set idle")
		self.i2cs.stop()
		print("Listening for start")
		cmd = bytearray(b'\xff')
		while cmd == bytearray(b'\xff'):
			try:
				self.i2cs.readinto(cmd)
			except:
				pass
		print('command: ', cmd)

		# self.i2cs.awaitStart()
		# print("reading byte")
		# address = self.i2cs.readByte()
		# print("sending ack")
		# self.i2cs.sendAck(0)

		# if bit 1 is off, we are reading
		# if bit 1 is on, we are writing 
		# writing = address & 0x01
		# address = address >> 1 
		# print("start: addr:",hex(address),"r/w:", writing)
		# incoming.set()

	def i2c_handler(self):
		while True:
			print("starting callback")
			# await incoming.wait()
			self.callback()
			print("read cmd")
			cmd = self.i2cs.readByte()
			self.i2cs.sendAck(0)
			print("command sent:", cmd)
			

