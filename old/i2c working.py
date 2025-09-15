

# i2cslave.py
#LUA-Pins     D0 D1 D2 D3 D4 D5 D6 D7 D8
#ESP8266 Pins 16  5  4  0  2 14 12 13 15 

from machine import Pin
from time import sleep_us

class I2CS:

	def __init__(self,scl=18,sda=19,freq=400000,hwadr=42):
		self.clock=Pin(scl,Pin.IN)
		self.data=Pin(sda,Pin.IN)
		self.freq=freq
		self.HWADR=hwadr
		self.puls=int(1000000/freq/2) #us
		self.stop=False
		print("Secondary started @ {} Hz".format(freq))
		
	def devAddress(self,adr=None):
		if adr is None:
			return self.HWADR
		else:
			self.HWADR = (adr & 0xff)
	
	def frequency(self,freq=None):
		if freq is None:
			return self.freq
		else:
			self.freq = freq
			self.pulse = int(1000000/freq/2)

	def setIdle(self):
		self.clock(Pin.IN)
		self.data(Pin.IN)

	def waitDataLow(self):
		while self.data.value()==1:
			pass
		
	def waitClockLow(self):
		while self.clock.value()==1:
			pass

	def waitClockHigh(self):
		while self.clock.value()==0:
			pass
		
	def awaitStart(self):
		while self.clock.value()==1:
			if self.data.value()==0:
				while self.clock.value()==1:
					pass

	def awaitStop(self):
		self.waitDataLow()
		self.waitClockHigh()
		sleep_us(self.pulse * 2)
		return self.data.value() == 1

	def readByte(self):
		byte=0
		self.stop=False
		for i in range(8):
			self.waitClockHigh()
			byte = ((byte ) << 1 ) | self.data.value()
			self.waitClockLow()
		return byte

	def writeByte(self,byte):
		self.waitClockLow()
		self.data.init(Pin.OUT)
		mask=0x80
		for i in range(0,8):
			bit=byte & mask
			if bit:
				self.data.value(1)
			else:
				self.data.value(0)
			mask=mask >> 1
			self.waitClockHigh()
			self.waitClockLow()
		self.data.init(Pin.IN)

	def sendAck(self,ack):
		self.waitClockLow()
		self.data.init(Pin.OUT,value=ack) # access data
		self.waitClockHigh()
		self.waitClockLow()
		self.data.init(Pin.IN)# release data
		
	def awaitAck(self):
		self.waitClockLow()
		self.waitClockHigh()
		ackBit=self.data.value()
		self.waitClockLow()
		return ackBit

"""
commands:
- send rtc

"""

#### RTC from ESP8266 (slave)
from machine import Pin, RTC
from uasyncio import asyncio
import asyncio

# set to start listening i2c channel by irq callback
incoming = asyncio.Event()

class I2CRTC:
	def __init__(self, scl=0, sda=2) -> None:
		self.i2cs = I2CS(scl=scl, sda=sda)
		self.sda = Pin(sda)
		self.scl = Pin(scl)
		self.sda.irq(trigger=Pin.IRQ_FALLING, handler=self.callback)
		self.i2cs.setIdle()

	if hwa==slave.HWADR: # wenn wir gemeint sind, dann
		if rw==0: # befehl empfangen, decodieren, ausfuehren
			print("W")
			cmd=slave.readByte() # Kommandobyte lesen
			slave.sendAck(0)
			print(hex(hwa), hex(cmd))

	def callback(self, id):
		self.i2cs.awaitStart()
		address = self.i2cs.readByte()
		self.i2cs.sendAck(0)

		# if bit 1 is off, we are reading
		# if bit 1 is on, we are writing 
		writing = address & 0x01
		address = address >> 1 
		print("HWADR:",hex(address),writing)
		incoming.set()

	async def i2c_handler(self):
		while True:
			await asyncio.wait_for(incoming)
			cmd = self.i2cs.readByte()
			print("command sent:", cmd)
			incoming.clear()

# slave.py
#LUA-Pins     D0 D1 D2 D3 D4 D5 D6 D7 D8 RX TX
#ESP8266 Pins 16  5  4  0  2 14 12 13 15  3  1
#Achtung      hi sc sd hi hi          lo hi hi
from machine import SoftI2C, Pin, ADC
from dht20 import DHT20
# from i2cslave import I2CSLAVE
from struct import pack

# Verbindung zum DHT20
i2c=SoftI2C(Pin(5),Pin(4),freq=100000)

# Verbindung zum Master
hwadr=0x63
slave=I2CSLAVE(scl=12,sda=13,freq=100,hwadr=hwadr)

relais=Pin(0,Pin.OUT,value=0)
relaisState=0

dht20=DHT20(i2c)
temperatur=None
feuchte=None

kontakt=Pin(2,Pin.IN)

ldr=ADC(0)

# Kommando-Register
cmdReg=None
val=None
# Kommandos
readLight = const(0x01)
readTemp  = const(0x02)
readHum   = const(0x04)
readKontakt=const(0x08)
relaisOn  = const(0x10)
relaisOff = const(0x20)

print("Program started ...")

def getLight():
	return pack("H",(1024-ldr.read())) # Normieren auf ein Byte

def getTemp():
	return pack("f",dht20.temperature)

def getHum():
	return pack("f",dht20.humidity)

def getTuerKontakt():
	return pack("b",kontakt.value())

def relaisSwitch(val):
	relais.value(val)
	return pack("b",relais.value())

def relaisStatus():
	return pack("b",relais.value())

# Main loop
while 1:
	slave.setIdle()
	slave.awaitStart()
	hwa=slave.readByte()
	slave.sendAck(0)
	rw=hwa & 0x01 # Richtungsbit isolieren
	hwa=hwa>>1 # 7-Bitadresse bilden
	print("HWADR:",hex(hwa),rw)
	if hwa==slave.HWADR: # wenn wir gemeint sind, dann
		if rw==0: # befehl empfangen, decodieren, ausfuehren
			print("W")
			cmd=slave.readByte() # Kommandobyte lesen
			slave.sendAck(0)
			print(hex(hwa), hex(cmd))
			cmdReg=cmd
			if cmd==readLight:
				val=getLight()
			elif cmd==readTemp:
				val=getTemp()
			elif cmd==readHum:
				val=getHum()
			elif cmd==readKontakt:
				val=getTuerKontakt()
			elif cmd==relaisOn:
				val=relaisSwitch(1)
			elif cmd==relaisOff:
				val=relaisSwitch(0)
			else:
				pass
			cmdReg=0
			
		else: # Daten senden
			for i in range(len(val)):
				slave.writeByte(val[i])
				ack=slave.awaitAck()
				
	if slave.awaitStop():
		slave.setIdle()


		





#################################################

#SEND 8266

from machine import I2C, Pin
import time

# Initialize I2C
i2c = I2C(scl=Pin(0), sda=Pin(2))

def send_message(address, message):
	i2c.writeto(address, message)

# Example usage
address = 0x42  # I2C address of the receiver device
message = "Hello, Device 2!"

def send():
	while True:
		send_message(address, message)
		print("Message sent:", message)
		time.sleep(5)  # Send message every 5 seconds


# RECV ESP32

from machine import I2C, Pin
import time

# Initialize I2C
i2c = SoftI2C(scl=Pin(2), sda=Pin(4))

def receive_message(address, num_bytes):
	return i2c.readfrom(address, num_bytes)

# Example usage
address = 0x42  # I2C address of this device
num_bytes = 32  # Number of bytes to read

while True:
	try:
		message = receive_message(address, num_bytes)
		print("Message received:", message.decode('utf-8'))
	except OSError:
		print("No message received.")
	time.sleep(5)  # Check for message every 5 seconds
