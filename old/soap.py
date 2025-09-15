# soap.py

from core import info
from hass import ha_setup

from sr04 import SR04
from pwmstatus import PWMStatus
from machine import Pin
from time import sleep
from device import Device

dispense_seconds = 2

# this esp32-wroom
trig_pin = 40
echo_pin = 39
motor_pin = 37
green_pin = 17
blue_pin = 21

info(f'sr04: trig: {trig_pin}, echo: {echo_pin}, motor: {motor_pin}, green_led: {green_pin}, blue_led: {blue_pin}' )

sensor = SR04("kitchen_soap", trig_pin, echo_pin )

motor = Pin(motor_pin, Pin.OUT)
motor.off()

wait_trigger_led = PWMStatus(green_pin, brightness=30)
wait_clear_led = PWMStatus(blue_pin, brightness=50)

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

# # soap.py

# from machine import Pin
# from time import sleep, ticks_us, sleep_us
# from core import info
# from sr04 import SR04


# sensor = SR04("soap", 40,39)
# info("sr04 set: trig pin: 40, echo pin: 39")

# motor = Pin(37, Pin.OUT)
# motor.off()
# info("motor pin: 37 - output set")

# while True:
# 	try:
# 		info("waiting for trigger")
# 		sensor.wait_trigger()
# 		info("Soap dispensing")
# 		motor.on()
# 		sleep(2)
# 		motor.off()
# 		info("waiting for clear")
# 		sensor.wait_clear()
# 	except KeyboardInterrupt:
# 		info("Keyboard - quit")
# 		break
# 	except:
# 		info("Unknown error caught!")
