# soapduo.py

# Do first in case of reboot!
from machine import Pin, SoftI2C
dishsoap_gpio = 6
dishsoap_pin = Pin(dishsoap_gpio, Pin.OUT)
dishsoap_pin.off()

handsoap_gpio = 7
handsoap_pin = Pin(handsoap_gpio, Pin.OUT)
handsoap_pin.off()

from versions import versions
versions[__name__] = 12
# 10: webconfig and no ha_setup
# 11: fixed some issues with logging
# 12: fixed i2c mix and added red pin for motor on

from logger import info, error
from pwmstatus import PWMStatus
import asyncio

from time import sleep
from device import Device

dispense_ms = 1000

red_gpio = 5
green_pin = 11
blue_pin = 10

info(f'dishsoap_pin: {dishsoap_pin}, handsoap_pin: {handsoap_pin}' )
info(f'red_led: {red_gpio}, green_led: {green_pin}, blue_led: {blue_pin}' )
info(f'dispense_seconds: {dispense_ms}' )

wait_trigger_led = PWMStatus(green_pin, brightness=30)
wait_clear_led = PWMStatus(blue_pin, brightness=50)

red_pin = Pin(red_gpio, Pin.OUT)
red_pin.off()

from vl53l0x import VL53L0X

try:
	dish_vlx_i2c = SoftI2C(scl=Pin(8), sda=Pin(9))
	dish_sensor = VL53L0X("dishsoap", dish_vlx_i2c)

	dishsoap_uses = Device("kitchen_dishsoap_uses", "0", units="count", save_state=True)

except:
	error("dishsoap: initialization failed")

try:
	hand_vlx_i2c = SoftI2C(scl=Pin(12), sda=Pin(13))
	hand_sensor = VL53L0X("handsoap", hand_vlx_i2c)

	handsoap_uses = Device("kitchen_handsoap_uses", "0", units="count", save_state=True)

except:
	error("handsoap: initialization failed")

async def handle_dispense(sensor, motor, uses):
	name = uses.name
	info(f"handle_dispense: {name}: running")
	while True:

		# turn on green glow while waiting for trigger
		info(f"handle_dispense: {name}: waiting for trigger")
		wait_trigger_led.on()
		await sensor.wait_for(in_range=True, count=3)
		wait_trigger_led.off()

		info(f"handle_dispense: {name}: Soap dispensing")
		red_pin.on()
		motor.on()
		#sleep(dispense_seconds)
		await sensor.wait_for(in_range=False, timeout_ms=dispense_ms, count=1)
		motor.off()
		red_pin.off()

		info(f"handle_dispense: {name}: waiting for all clear")

		# turn on blue glow while waiting to clear
		wait_clear_led.on()
		await sensor.wait_for(in_range=False)
		uses.set_state(int(uses.state) + 1)
		info(f"handle_dispense: {name}: dispense count: {uses.state}" )
		wait_clear_led.off()

asyncio.create_task(handle_dispense(dish_sensor, dishsoap_pin, dishsoap_uses))
asyncio.create_task(handle_dispense(hand_sensor, handsoap_pin, handsoap_uses))

