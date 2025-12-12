# soap12v.py
# lidar sensor with separate 12v motor dc source

# Do first in case of reboot!
from machine import Pin, I2C
motor_pin = 7
motor = Pin(motor_pin, Pin.OUT)
motor.off()

from versions import versions
versions[__name__] = 12
# 10: conforms to new standard
# 11: short counts on and off
# 12: dispense time 500 ms

from logger import info, debug, error
from pwmstatus import PWMStatus
import asyncio
from time import sleep
from device import Device

dispense_ms = 500
red_pin = 1
green_pin = 2
blue_pin = 3

info(f'motor_pin: {motor_pin}, red_led: {red_pin}, green_led: {green_pin}, blue_led: {blue_pin}' )
info(f'dispense_seconds: {dispense_ms}' )

wait_trigger_led = PWMStatus(green_pin, brightness=30)
wait_clear_led = PWMStatus(blue_pin, brightness=50)

#########################
# lidar setup
########################

from vl53l0x import VL53L0X
from machine import I2C, Pin

vlx_i2c = I2C(scl=Pin(8), sda=Pin(9))
sensor = VL53L0X("soap12v_lidar", vlx_i2c)

dispense_counts = Device("hand_soap_uses", "0", units="count", save_state=True)

async def start():
	while True:

		# turn on green glow while waiting for trigger
		info("waiting for trigger")
		wait_trigger_led.on()
		await sensor.wait_for(in_range=True, count=3)
		wait_trigger_led.off()

		info("Soap dispensing")
		motor.on()
		#sleep(dispense_seconds)
		await sensor.wait_for(in_range=False, timeout_ms=dispense_ms, count=1)
		motor.off()

		info("waiting for clear")

		# turn on blue glow while waiting to clear
		wait_clear_led.on()
		await sensor.wait_for(in_range=False)
		dispense_counts.set_state(int(dispense_counts.state) + 1)
		info("dispense count: {}".format(dispense_counts.state) )
		wait_clear_led.off()

asyncio.create_task(start())
