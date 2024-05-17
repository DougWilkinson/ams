# analog.py

version = (2,0,7)

import uasyncio as asyncio
from sys import platform
from machine import Pin, ADC
from time import ticks_diff, ticks_ms
from device import Device
from hass import ha_setup
import asyncio

def init(name, pin=None, k=159.3, units="v"):
	if 'esp32' in platform:
		if pin:
			adc = ADC(Pin(pin))
		else:
			raise UserWarning("pin # needed on esp32")
	if 'esp8266' in platform:
		adc = ADC(0)
	analog = Device(name, "0", units=units, notifier_setup=ha_setup)
	asyncio.create_task(adc_handler(analog, adc, k))			

async def adc_handler(analog, adc, k):
	while True:
		analog.set_state(round(adc.read()/k,2) )
		await asyncio.sleep(60)
