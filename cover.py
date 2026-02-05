# cover.py

# Cover("name", mover=None, checker=None)
# mover could be a stepper, servo or motor
# mover methods: move_forward(checker), move_backward(checker)

# checker can be a limit switch or encoder (something that is polled while the mover is moving something)
# defined with a step count and a timeout (as appropriate)

# limit is similar to checker but used instead of or in addition to checker
# it must be "started" and checked for "completed"

from versions import versions
versions[__name__] = 12
# 10: using webconfig (no hass_setup)
# 11: fixed state values for saved vs setting
# 12: added "opening" and "closing" states before final state

import asyncio
from logger import info, error, debug
from system import start
from device import Device

class Cover:
	def __init__(self, name, mover, checker=None, open_limit=None, close_limit=None ):
		
		self.mover = mover
		self.checker = checker
		self.open_limit = open_limit
		self.close_limit = close_limit
		self.state = Device(name, "unknown", dtype="cover", save_state=True, needs_publishing=True )
		start(self.move_handler )

	async def move_handler(self):

		# should be lower case "open" or "closed"
		current_state = self.state.state
		info("cover: {} - current_state: {}".format(self.state.name, self.state.state))
		
		async for _, ev in self.state.q:
			
			# continue if not open or close in event
			if "OPEN" not in ev and "CLOSE" not in ev:
				error("cover: {} - state invalid: {}".format(self.state.name, ev))
				# if not a valid state change, set back to current state and cancel save
				self.state.set_state(current_state)
				self.state.trigger_save.clear()
				continue

			# convert new state to match the saved state (what HA expects in final published state)
			# HA expects lowercase "open" or "closed" in published state

			if ev == "OPEN":
				new_save_state = "open"

			if ev == "CLOSE":
				new_save_state = "closed"

			if new_save_state == current_state:
				debug("cover: state already set to: {}".format(new_save_state))
				self.state.set_state(current_state)
				self.state.trigger_save.clear()
				continue

			info("cover: {} - state changing: {} -> {}".format(self.state.name, current_state, new_save_state))
			
			self.state.set_state("opening" if new_save_state == "open" else "closing")
			await asyncio.sleep(.1)

			if new_save_state == "open":
				self.mover.move_forward(self.checker, limit=self.open_limit)
			
			if new_save_state == "closed":
				self.mover.move_backward(self.checker, limit=self.close_limit)

			info("cover: {} - moved to: {}".format(self.state.name, new_save_state))
			self.state.set_state(new_save_state)
			current_state = new_save_state
			