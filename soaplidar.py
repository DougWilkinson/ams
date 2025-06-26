# soaplidar.py
# new version with lidar sensor

from versions import versions
versions[__name__] = 1

from core import info, latch, started
from hass import ha_setup

from sr04 import SR04
from machine import Pin, I2C
from pwmstatus import PWMStatus

from time import sleep
from device import Device

dispense_seconds = 2

# this esp32-wroom
motor_pin = 7

red_pin = 1
green_pin = 2
blue_pin = 3

info(f'motor_pin: {motor_pin}, red_led: {red_pin}, green_led: {green_pin}, blue_led: {blue_pin}' )
info(f'dispense_seconds: {dispense_seconds}' )

motor = Pin(motor_pin, Pin.OUT)
motor.off()

wait_trigger_led = PWMStatus(green_pin, brightness=30)
wait_clear_led = PWMStatus(blue_pin, brightness=50)

#########################
# lidar test
########################

from vl53l0x import VL53L0X
from machine import I2C, Pin

vlx_i2c = I2C(scl=Pin(8), sda=Pin(9))
sensor = VL53L0X("soap_lidar", vlx_i2c)

async def start(hostname):
	started(hostname)
	await latch.wait()


dispense_counts = Device("kitchen_soap_uses", "0", units="count", save_state=True, notifier_setup=ha_setup)

async def start(hostname):
	while True:
		try:

			# turn on green glow while waiting for trigger
			info("waiting for trigger")
			wait_trigger_led.on()
			await sensor.wait_trigger()
			wait_trigger_led.off()

			info("Soap dispensing")
			motor.on()
			sleep(dispense_seconds)
			motor.off()

			info("waiting for clear")

			# turn on blue glow while waiting to clear
			wait_clear_led.on()
			await sensor.wait_clear()
			dispense_counts.set_state(int(dispense_counts.state) + 1)
			info("dispense count: {}".format(dispense_counts.state) )
			wait_clear_led.off()

		except KeyboardInterrupt:
			info("Keyboard - quit")
			break
		except:
			info("Unknown error caught!")

