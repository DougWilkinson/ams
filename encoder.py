# encoder.py
# used for tracking gpio pin on/off changes
# for use as a checker with Cover class

from versions import versions
versions[__name__] = 10
# 10: using webconfig (no hass_setup)

from machine import Pin
import time
from logger import info, error, debug

# ticks are encoder transitions counted from 0 to 1
class Encoder:
	def __init__(self, enc_pin,timeout_ms=5000):
		self.enc_pin = Pin(enc_pin, Pin.IN)
		self.encoder_state = 0
		self.moved_ticks = 0
		self.last_tick = time.ticks_ms()
		self.ticks_to_move = 0
		self.timeout_ms = timeout_ms

	def start(self, ticks_to_move, timeout_ms=5000):
		self.ticks_to_move = ticks_to_move
		self.timeout_ms = timeout_ms
		self.last_tick = time.ticks_ms()
		self.encoder_state = self.enc_pin.value()
		self.moved_ticks = 0
		info("encoder: started: pin_state={}, last_tick={}".format(self.encoder_state, self.last_tick))

	# returns 0 if not done
	# returns negative count if done (timed out)
	# returns positive count if done (reached ticks_to_move)
	def completed(self) -> int:
		
		# if timeout is used, check elapsed time and return negative count if over timeout
		if self.timeout_ms:
			diff = time.ticks_ms() - self.last_tick
			if diff > self.timeout_ms:
				error("encoder: timed out!")
				if not self.moved_ticks:
					return -1
				return - self.moved_ticks
			
		# check for and count transition from low to high
		if not self.encoder_state and self.enc_pin.value():
			debug("encoder: elapsed: {} ms".format(diff) )
			self.last_tick = time.ticks_ms()
			self.moved_ticks += 1
		
		self.encoder_state = self.enc_pin.value()
		
		if  self.ticks_to_move == self.moved_ticks:
			debug("encoder: ticks_to_move reached")
			return self.moved_ticks
		
		return 0	
