# soap.py

from machine import Pin
from time import sleep, ticks_us, sleep_us
from core import info
from sr04 import SR04

sensor = SR04("soap", 40,39)
info("sr04 set: trig pin: 40, echo pin: 39")

motor = Pin(37, Pin.OUT)
motor.off()
info("motor pin: 37 - output set")

while True:
	try:
		info("waiting for trigger")
		sensor.wait_trigger()
		info("Soap dispensing")
		motor.on()
		sleep(2)
		motor.off()
		info("waiting for clear")
		sensor.wait_clear()
	except KeyboardInterrupt:
		info("Keyboard - quit")
		break
	except:
		info("Unknown error caught!")