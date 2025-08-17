# cubeclock.py
# super mini s3 and sh1106 in office cube

from versions import versions
versions[__name__] = 1

from machine import Pin, SoftI2C
import asyncio
import time

from hass import subscribe_name
from settings import info, debug, error, config, start, get_profiles
from touchpin import TouchPin
from sh1106 import SH1106_I2C
from clock3da import Clock3D

from device import Device
from menu import Menu

# latch = asyncio.Event() 

info("cubeclock: loading")

sh1106_i2c = SoftI2C(scl=Pin(12),sda=Pin(13))

sh_display = SH1106_I2C(128, 64, sh1106_i2c )

# sh_clock = BlitClock("sh1106", width=64, height=64, display=sh_display, bitmap=MONO_VLSB, hand=2)

sh_clock = Clock3D("cubeclock", display=sh_display, scale=0.44)

forecast = Device("hass/weather/forecast", "" )
subscribe_name(forecast)

temperature = Device("hass/weather/temperature", "" )
subscribe_name(temperature)

next_button = TouchPin("up_button", pin=6, on_value=19500, off_value=18500)
select_button = TouchPin("down_button", pin=7, on_value=18000, off_value=16000)	

clock_menu = [ [ "profiles", "12/24", "style", "exit" ], 
			 get_profiles() + [ "back" ], 
			 [ "12", "24", "back" ],	
			 [ "flip", "static", "back" ] ]

def set_hour_style(hour_style):
	pass

def set_clock_style(clock_style):
	pass

function_index = { "profiles": config.set_as_default, "12/24": set_hour_style, "style": set_clock_style }

menu = Menu(clock_menu)

update_menu_display = asyncio.Event()

def clear_menu_display(show=True):
	# clear top row
	sh_display.fill_rect(0, 0, 128, 8, 0)

	# clear bottom row
	sh_display.fill_rect(0, 56, 128, 64, 0)

	if show:
		sh_display.show()

async def update_weather():
	info("update_weather: running")
	while True:
		async for _, ev in forecast.q:
			if menu.active:
				continue
			clear_menu_display(show=False)
			sh_display.text(forecast.state, 0, 56)
			sh_display.text(temperature.state, 128 - (8 * len(temperature.state) ), 0)
			sh_display.show()

		await temperature.wait()

async def show_clock_menu():
	info("show_clock_menu: running")
	while True:

		debug("show_clock_menu: waiting for update_menu_display")
		await update_menu_display.wait()
		update_menu_display.clear()

		debug("show_clock_menu: clearing and updating display")
		clear_menu_display(show=False)

		if menu.active:
			# display value from menu on top row
			sh_display.text(clock_menu[menu.row][menu.item], 0, 0)

			# display text for select/set button on bottom row
			if menu.row == 0:
				sh_display.text("select", 0, 56)
			else:
				sh_display.text("set", 0, 56)
		else:
			# show date, weather and temperature
			sh_display.text(forecast.state, 0, 56)
			sh_display.text(temperature.state, 128 - (8 * len(temperature.state) ), 0)

		sh_display.show()

async def next_button_handler():
	info("next_button_handler: running")
	while True:
		await next_button.wait()

		asyncio.create_task(menu_inactive_timeout())

		update_menu_display.set()
		menu.next_button_handler()

async def select_button_handler():
	info("select_button_handler: running")
	while True:
		await select_button.wait()

		asyncio.create_task(menu_inactive_timeout())
		
		# returns a tuple with row and item if option is selected
		# otherwise returns None
		value = menu.select_button_handler()
		debug("value: {}".format(value))

		# call function based on returned tuple as index
		if value:
			# # don't display normal values from menu, override below
			# update_menu_display.clear()
			debug("function name: {} value: {}".format(clock_menu[0][value[0]], value[1]) )

			# display setting and value, call related function and wait
			clear_menu_display(show=False)
			sh_display.text("Setting: {}".format(clock_menu[0][value[0]]), 0, 0)
			sh_display.text("Value: {}".format(clock_menu[value[0]][value[1]]), 0, 56)
			sh_display.show()
			function_index[clock_menu[0][value[0]]](clock_menu[value[0]][value[1]] )

			debug("select_button_handler: update_menu_display.is_set = {}".format(update_menu_display.is_set() ) )
			continue

		debug("select_button_handler: no value: update_menu_display.set = {}".format(update_menu_display.is_set() ) )
		update_menu_display.set()

timeout_waiting = asyncio.Event()

async def menu_inactive_timeout():
	if timeout_waiting.is_set():
		debug("menu_inactive_timeout: already checking for inactivity")
		return
	timeout_waiting.set()

	debug("menu_inactive_timeout: new: wait for inactivity")
	while time.time() - menu.last_event_seconds < 6:
		await asyncio.sleep(1)

	debug("menu_inactive_timeout: disabling menu and updating display")
	menu.active = False
	update_menu_display.set()
	timeout_waiting.clear()

start(update_weather)
start(show_clock_menu)
start(next_button_handler)
start(select_button_handler)

# # raw flag value for timezone saved here
# timezone = Device("set_timezone", "29", save_state=True)

# def show_timezone():
# 	sh_display.fill_rect(0, 0, 128, 8, 0)
# 	sh_display.text("timezone: {}   ".format(get("timezone") - 24), 0, 0)
# 	timezone.set_state(get("timezone") )

# async def increase_timezone():
# 	while True:
# 		await up_button.wait()
# 		set("timezone", get("timezone") + 1)
# 		show_timezone()

# async def decrease_timezone():
# 	while True:
# 		await down_button.wait()
# 		set("timezone", get("timezone") - 1)
# 		show_timezone()

# asyncio.create_task(increase_timezone())
# asyncio.create_task(decrease_timezone())

# show_timezone()

# async def start(hostname):
# 		await latch.wait()
