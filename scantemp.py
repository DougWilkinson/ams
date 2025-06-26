# scantemp.py
# Use a servo motor to scan temperatures


from machine import Pin
from time import sleep, ticks_us, sleep_us
from core import info
# from sr04 import SR04
import asyncio
from mlx90614 import MLX90614
from machine import SoftI2C

#dispense_seconds = 1

# test rig esp32-wroom
# trig_pin = 22
# echo_pin = 21
# motor_pin = 33

# kitchen dispenser w/ esp32-s2
# trig_pin = 40
# echo_pin = 39
# motor_pin = 37

# sensor = SR04("kitchen_soap", trig_pin, echo_pin, green=26, blue=27)

# info("sr04: trig: {}, echo: {}".format(trig_pin, echo_pin))

# motor = Pin(motor_pin, Pin.OUT)
# 
from machine import SoftI2C, Pin
mlx_i2c = SoftI2C(scl=Pin(18), sda=Pin(19))

from machine import SoftI2C, Pin
mlx_i2c = SoftI2C(scl=Pin(25), sda=Pin(32))
mlx = MLX90614()

def scan()

async def start(hostname):
	while True:
		try:
			await sensor.wait_clear()
		except KeyboardInterrupt:
			info("Keyboard - quit")
			break
		except:
			info("Unknown error caught!")