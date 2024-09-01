# dispenser.py

from versions import versions
versions[__name__] = 3
# 2 0 7: grams.set_state(0) to fix same value issue
# 208: rgb status fix

from time import sleep_ms
from machine import Pin
from core import info, started, error
from device import Device
from hass import ha_setup
import uasyncio as asyncio

class Dispenser():

	# display = alphanumeric display device is "string"
	# rgb = neopixel status values = "glow_green", "red_pulse", "busy"
	def __init__(self, name, display=None, rgb=None, grams="0", tray=None, motor_pin=5, hx_average=None ):
		self.motor_pin = Pin(motor_pin, Pin.OUT)
		self.motor_pin.off()
		started(name)

		#self.activate = Device(name + "/activate", state="", notifier_setup=ha_setup)
		self.grams = Device(name + "/grams", state=grams, units="g", notifier_setup=ha_setup)
		self.dispensed = Device(name + "/dispensed", state="0", units="g", ro=True, notifier_setup=ha_setup)
		# rgb is a device where string is set
		# glow_one, glow_two, glow_green, pulse_red, unknown
		self.rgb_status = rgb
		# average is callable returning rolling average
		self.hx_average = hx_average
		# tray is a callable returning boolean where if True, tray is in place/detected
		self.tray = tray
		# flick is time motor is off between measurements
		self.flick_ms = 50
		self.rawvalue = 0
		self.sorted_vals = []
		self.values = [0, ] * 3
		self.actual = 0
		# flag set when something changes
		self.error = ""
		self.display = display
		# start waiting for state change
		asyncio.create_task(self._dispense_grams() )
		asyncio.create_task(self._tray_status() )

	async def _dispense_grams(self):
		async for _, msg in self.grams.q:
			info("dispenser: activate: msg: {}".format(msg))
			self.grams.set_state(0)
			#self.activate.set_state("OFF")
			#print("activate: ", self.activate.state, self.activate.publish.is_set())
			try:
				grams = int(msg)
			except ValueError:
				error("error converting grams value to int")
				continue
			if self.rgb_status:
				self.rgb_status.set_state("steady")
			self.actual, self.error = await self.measure(grams)
			if self.error:
				if self.display:
					self.display.put("state", "err - {} g - ".format(self.actual) )
				if self.rgb_status:
					self.rgb_status.set_state("pulse_red")
			else:
				self.dispensed.set_state(self.actual)
				if self.display:
					self.display.set_state(self.actual )
				if self.rgb_status:
					if grams == 17:
						self.rgb_status.set_state("glow_one")
					if grams == 34:
						self.rgb_status.set_state("glow_two")
			info("dispenser: waiting for tray off")
			while self.tray():
				await asyncio.sleep(1)
			self.grams.set_state(0)

	
	async def _tray_status(self):
			while True:
				info("dispenser: tray on - hx: {}".format(self.hx_average() ) )
				if self.rgb_status:
					self.rgb_status.set_state("glow_green")
				while self.tray():
					await asyncio.sleep(1)
				info("dispenser: tray off - hx: {}".format(self.hx_average() ) )
				if self.rgb_status:
					self.rgb_status.set_state("pulse_red")
				while not self.tray():
					await asyncio.sleep(1)
			
	async def measure(self, grams=17, flick=100, waitsec=2):
		#info("target: {} cycles".format(self.cycles.state) )
		rgrams = 0
		error_msg = None
		try:
			tare = self.hx_average()
			avg = tare
			last = tare
			low_count = 0

			info("  rgrams    grams      avg     last     diff    low_c")			
			# flick until cycles seen or bin is full
			while avg - tare < grams:
				if not self.tray():
					error_msg = "no tray"
					raise UserWarning
				if low_count > 12:
					error_msg = "no beans"
					raise UserWarning
				self.motor_pin.on()
				# run continuously until 80%
				# Then start flicking by turning off motor and waiting
				if (avg-tare) / grams >= 0.8:
					sleep_ms(flick)
					self.motor_pin.off()			
					await asyncio.sleep(waitsec)
				#info("{} / {} / {}".format(avg, last, avg-last) )
				if avg - last < .3:
					low_count += 1
				else:
					low_count = 0
				last = avg

				# put sleep here before taking measurement for max settling
				await asyncio.sleep_ms(500)
				avg = self.hx_average()
				rgrams = avg-tare
				info("{:>8.2f},{:>8.2f},{:>8.2f},{:>8.2f},{:>8.2f},{:>8.2f}".format(rgrams, grams, avg, last, avg-last, low_count) )							

			info("dispenser: measure: Success: {} grams".format(rgrams))
		except:
			error("dispenser: measure: {} - {}".format(rgrams, error_msg))

		self.motor_pin.off()
		return str(rgrams), error_msg
