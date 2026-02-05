# steppermotor.py
# mover methods: move_forward(checker, steps), move_backward(checker, steps)

from versions import versions
versions[__name__] = 11
# 10: using webconfig (no hass_setup)
# 11: added limit support for limit switches

from machine import Pin
import time
from logger import info, error, debug

# checker to complete after max steps
# checker is called after each step to check if the move is complete
class MaxSteps:

	def start(self, max_steps):
		self.steps_moved = 0
		self.max_steps = max_steps
	
	def completed(self):
		if self.steps_moved == self.max_steps:
			return self.max_steps
		self.steps_moved += 1
		return 0
	
class Limit:
	def start(self):
		pass

	# never reaches limit
	def completed(self):
		return 0

class StepperMotor:
	def __init__(self, enable_pin=4, step_pin=5, dir_pin=6, 
				 delay=1250, backoff_steps=300, max_steps=1000):

		self.enable_pin = Pin(enable_pin, Pin.OUT)
		self.enable_pin.value(1)
		self.dir_pin = Pin(dir_pin, Pin.OUT)
		self.step_pin = Pin(step_pin, Pin.OUT)
		self.limit_pin = None
		self.invert_limit = False
		self.delay = delay
		self.backoff_steps = backoff_steps
		self.max_steps = max_steps

	def onestep(self):
		self.step_pin.value(1)
		self.step_pin.value(0)
		time.sleep_us(self.delay)
	
	def move_forward(self, checker=None, steps=None, limit=None):
		self.dir_pin.value(1)
		self._move(checker, steps, limit)

	def move_backward(self, checker=None, steps=None, limit=None):
		self.dir_pin.value(0)
		self._move(checker, steps, limit)

	def _move(self, checker, steps, limit):
		
		if not steps:
			steps = self.max_steps

		# use MaxSteps as default checker
		if checker is None:
			checker = MaxSteps()

		# use Limit as default limit
		if limit is None:
			limit = Limit()
		
		# start the checker at zero, must provide max thing you are counting
		checker.start(steps)

		# initialize limit check
		limit.start()

		# enable motor		
		self.enable_pin.value(0)

		info("stepper moving: {} steps".format(steps))

		# keep stepping until checker.completed is non-zero
		while not checker.completed() and not limit.completed():
			self.onestep()
		
		# if timeout or limit checker reached before max steps, back off a little
		if checker.completed() < 0 or limit.completed():
			error("stepper limit or timeout reach: moved: {} steps".format(checker.completed()) )
			info("stepper backing off: {} steps".format(self.backoff_steps) )
			
			# reverse direction and move backoff_steps
			self.dir_pin.value(not self.dir_pin.value())
			checker.start(self.backoff_steps)

			# move until not at limit anymore
			while not checker.completed():
				self.onestep()
			
			debug("stepper backed off: {} steps".format(checker.completed() ) )
		else:
			info("stepper moved: {} steps".format(checker.completed() ) )

		# disable motor
		self.enable_pin.value(1)
