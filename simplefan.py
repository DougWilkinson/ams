
from machine import PWM, Pin, deepsleep
import time
trigger = Pin(0, Pin.IN)
servo = PWM(Pin(3))
servo.freq(50)
servo.duty(75)

power_enable = Pin(5, Pin.OUT)
power_enable.on()

while True:
	servo.duty(66)
	time.sleep(3)

	servo.duty(75)
	time.sleep(3)

	servo.duty(83)
	time.sleep(3)

	servo.duty(75)
	time.sleep(3)

