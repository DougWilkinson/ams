# candy.py

from versions import versions
versions[__name__] = 6
# 5: converted to new standard (no hass_setup)
# 6: moved to s3mini hardware


from machine import Pin

# pin 23 --> 8
motor_pin = Pin(8, Pin.OUT)
motor_pin.off()

from tm1637 import TM1637
from binary import Binary
from switch import Switch


# old hardware 
# display = TMClock(data_pin=0, clock_pin=4, brightness=5)
# tray_sensor = Tray("candy_tray", pin=13, invert=True)
# button = Binary("candy_button", pin=15, invert=False)
# dispense = Switch("candy_dispense", switch_pin=5, off_delay=3, trigger_device=button.state)

# pin 21 --> 6
# pin 22 --> 7
display = TM1637("candy",data_pin=6, clock_pin=7, brightness=5)

# pin 19 --> 5
tray_sensor = Binary("candy_tray", pin=5, invert=True)

# pin 18 --> 4
button = Binary("candy_button", pin=4, invert=False)

dispense = Switch("candy_dispense", motor_pin, off_delay=3, trigger_device=button.state, condition=tray_sensor.state)

