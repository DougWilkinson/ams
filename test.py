# test.py

from machine import SoftI2C, Pin

def i2c_slave(scl=5, sda=4, freq=500000):
	# Configure the I2C interface
	i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda), freq=freq)
	
	# Prepare the 10-byte data buffer to be sent
	data_buffer = bytearray([0xA0, 0xA1, 0xB0])

	while True:
		try:
			# Wait for the master to start communication
			#i2c.start()
			
			# Read the command from the master
			command = bytearray(1)
			i2c.readinto(command)
			print("command received: ", command)
			# Check if the command is the expected read command (0x42)
			if command[0] == 0x42:
				# Respond with the 10-byte data buffer
				print("acks from write: ", i2c.write(data_buffer) )
				
			# Stop the I2C communication
			#i2c.stop()
		
		except Exception as e:
			print("I2C communication error:", e)
			#i2c.stop()

class master:
	def __init__(self, freq=500000) -> None:
		self.i2c = SoftI2C(scl=Pin(2), sda=Pin(4), freq=freq)
		self.response = bytearray(10)

	def send(self, command=0x42):
		# try:
		# Send the command to the slave
		self.i2c.start()
		print("acks from write:", self.i2c.write(bytearray([command]) ) )
		#self.i2c.stop()
		
		# Read the response from the slave
		#self.i2c.start()
		self.i2c.readinto(self.response)
		self.i2c.stop()
		
		# Process the received response
		print("Received response from slave:", self.response)

