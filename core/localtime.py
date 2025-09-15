# localtime.py

from versions import versions
versions[__name__] = 1

import time

class LocalTime:
	def __init__(self, timezone):
		self.timezone = timezone

	def now(self):
		return time.localtime(time.time() + ((self.timezone - 24) * 3600) )

local_time = LocalTime(0)

def offset_time(timezone=None):
	if timezone is not None:
		local_time.timezone = timezone
	return local_time.now()
