# coffee_scale.py
# 2 button scale with sh1106 display

from versions import versions
versions[__name__] = 11
# 10: converted to new standard for device and hass
# 11: using low_power

from machine import Pin, SoftI2C
import asyncio

from logger import info, debug
from system import start, exception_handler
from events import low_power

from binary import Binary
from hx711a import HX711
from scale import Scale
from sh1106 import SH1106_I2C
from clock3dblit import Clock
from digits3d import generate_digits

# using esp32 S2 doesn't have as much horsepower
low_power.set()
rate_ms = 50

# offset was -151
# tried changing diff (was 2) and k (was 495)
hx = HX711(hxclock_pin=35, hxdata_pin=33, diff=1, samples=16, discard=4, rate_ms=rate_ms, k=498, offset=59000, min=0, max=5000)

sh1106_i2c = SoftI2C(scl=Pin(9),sda=Pin(7), freq=200000)

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

# scale to 0.4 for sh1106
digits = generate_digits(scale=0.4)

# y=21 for sh1106 centered with space above/below for small text
digit_y = 21
sh_clock = Clock("coffee_clock", sh_display, digits, x=0, y=digit_y)

# pullup = 2 for pullup resistor
# pullup = 1 for pull down resistor
tare_button = Binary("coffee_scale_tare", 5, pullup=2, invert=True)
units_button = Binary("coffee_scale_units", 3, pullup=2, invert=True)


def show_weight(value):

	# wait for the clock to stop	
	#await self.clock_stopped.wait()

	# clear the display buffer only
	sh_display.fill(0)

	# draw a big dot for decimal point
	# probably not scaled correctly
	sh_display.text(".",80,digit_y+8,1)
	sh_display.text(".",82,digit_y+8,1)
	sh_display.text(".",80,digit_y+10,1)
	sh_display.text(".",82,digit_y+10,1)

	# draw "grams" at top right
	sh_display.text("grams",80,0,1)

	# build the value string and take first 7 characters
	value_str = f"        {value:.2f}"[-8:]

	debug(f'show_weight: value_str: "{value_str}"')

	# leave a space for the "g" at the end
	x = 1

	# display the weight
	for i in range(8):

		# skip spaces and periods
		if value_str[i] == " " or value_str[i] == ".":
			x += 16
			continue
		
		if value_str[i] == "-":
			show_value = 11
		else:
			show_value = int(value_str[i])

		
		# draw the digit
		sh_display.blit(digits[show_value].from_blits[0], x, digit_y)

		x += 16
	
	sh_display.show()





@exception_handler
async def show_scale():
	info("show_scale: running")
	
	# used to display last known weight while clock is displayed
	last_stable_hx = 0

	while True:
		
		last_hx = hx.average()
		x = 1
		direction = 1
		# wait for change in scale or tare button is pressed
		# must change by 3 grams to count as a change
		while last_hx > hx.average() - 3 and last_hx < hx.average() + 3:
			if tare_button.pressed.is_set():
				tare_button.pressed.clear()
				hx.set_tare()
				break
			sh_display.fill_rect(0, 0, 128, 8, 0)
			sh_display.text(f"{last_stable_hx:.2f} g     ", x, 0, 1)
			x += direction
			if x > 90 or x < 2:
				direction = -direction

			await asyncio.sleep(0.5)

		# await tare_button.pressed.wait()
		debug("show_scale: waking up!")

		sh_clock.show_clock.clear()
		debug("show_scale: waiting for clock to stop")
		await sh_clock.clock_stopped.wait()

		inactive_seconds = 0
		last_hx = hx.average()
		while inactive_seconds < 30:

			debug("show_scale: reading scale")
			v = hx.average()
			if v - last_hx < 1:
				inactive_seconds += rate_ms/1000
				last_stable_hx = v
			else:
				inactive_seconds = 0
				last_hx = v

			debug(f"show_scale: {v}")
			show_weight(v)

			await asyncio.sleep(rate_ms/1000)

			if tare_button.pressed.is_set():
				tare_button.pressed.clear()
				hx.set_tare()
				inactive_seconds = 0

		debug("show_scale: returning to clock display")
		sh_clock.show_clock.set()

start(show_scale)