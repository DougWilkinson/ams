# soaptest.py

from versions import versions
versions[__name__] = 1

from core import info, latch, started
from hass import ha_setup

from sr04 import SR04
from pwmstatus import PWMStatus
from machine import Pin
from time import sleep
from device import Device

dispense_seconds = 2

# this esp32-wroom
trig_pin = 22
echo_pin = 21
motor_pin = 33
green_pin = 26
blue_pin = 27

#########################
# lidar test
########################

from vl53l0x import VL53L0X
from machine import I2C, Pin

vlx_i2c = I2C(scl=Pin(18), sda=Pin(19))
detector = VL53L0X("couch_lidar", vlx_i2c)

async def start(hostname):
	started(hostname)
	await latch.wait()




# info(f'sr04: trig: {trig_pin}, echo: {echo_pin}, motor: {motor_pin}, green_led: {green_pin}, blue_led: {blue_pin}' )

# kitchen dispenser w/ esp32-s2
# trig_pin = 40
# echo_pin = 39
# motor_pin = 37

##############################################
# uncomment below for soaptest using esp32-wroom
###############################################

# info(f'sr04: trig: {trig_pin}, echo: {echo_pin}, motor: {motor_pin}, green_led: {green_pin}, blue_led: {blue_pin}' )

# sensor = SR04("soap_test", trig_pin, echo_pin )

# motor = Pin(motor_pin, Pin.OUT)
# motor.off()

# wait_trigger_led = PWMStatus(green_pin, brightness=30)
# wait_clear_led = PWMStatus(blue_pin, brightness=50)

# dispense_counts = Device("dispense_counts", "0", units="count", save_state=True, notifier_setup=ha_setup)

# async def start(hostname):
# 	while True:
# 		try:

# 			# turn on green glow while waiting for trigger
# 			info("waiting for trigger")
# 			wait_trigger_led.on()
# 			await sensor.wait_trigger()
# 			wait_trigger_led.off()

# 			info("Soap dispensing")
# 			motor.on()
# 			sleep(dispense_seconds)
# 			motor.off()

# 			info("waiting for clear")

# 			# turn on blue glow while waiting to clear
# 			wait_clear_led.on()
# 			await sensor.wait_clear()
# 			dispense_counts.set_state(int(dispense_counts.state) + 1)
# 			info("dispense count: {}".format(dispense_counts.state) )
# 			wait_clear_led.off()

# 		except KeyboardInterrupt:
# 			info("Keyboard - quit")
# 			break
# 		except:
# 			info("Unknown error caught!")