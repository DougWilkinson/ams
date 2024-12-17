# soaptest.py

from machine import Pin
from time import sleep, ticks_us, sleep_us
from core import info
from sr04 import SR04
import uasyncio as asyncio

dispense_seconds = 1

# test rig esp32-wroom
trig_pin = 22
echo_pin = 21
motor_pin = 33

# kitchen dispenser w/ esp32-s2
# trig_pin = 40
# echo_pin = 39
# motor_pin = 37

sensor = SR04("kitchen_soap", trig_pin, echo_pin, green=26, blue=27)

info("sr04: trig: {}, echo: {}".format(trig_pin, echo_pin))

motor = Pin(motor_pin, Pin.OUT)
motor.off()
info("motor: {}".format(motor_pin))

async def start(hostname):
	while True:
		try:
			info("waiting for trigger")
			await sensor.wait_trigger()
			info("Soap dispensing")
			motor.on()
			sleep(dispense_seconds)
			motor.off()
			info("waiting for clear")
			await sensor.wait_clear()
		except KeyboardInterrupt:
			info("Keyboard - quit")
			break
		except:
			info("Unknown error caught!")