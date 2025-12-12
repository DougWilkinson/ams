# logger.py

from versions import versions
versions[__name__] = 11
# 1: started to separate console and logging from settings
# 10: refactored
# 11: revised color support and cleaned up end=end

from localtime import offset_time
from network import WLAN

from msgqueue import MsgQueue

# errors 0-1: red
# info 2-5: white
# debug 6-7: cyan
colors = ['\u001b[31m', '\u001b[31m', '\u001b[0m', '\u001b[0m', '\u001b[0m', '\u001b[0m', '\u001b[36m', '\u001b[36m']]

def strftime():
	month, day, year, hour, minute, second, _, _ = offset_time()
	return "{:02d}/{:02d}/{:02d}-T{:02d}:{:02d}:{:02d}".format( month, day, year, hour, minute, second )

class Logger:
	def __init__(self, log_level=7, buffer_size=100):
		self.log_level = log_level
		self.console_history = MsgQueue(buffer_size)

	def info(self, msg, log_level=2, end="\n"):
	
		# log all levels to buffer
		log_line = "{}: {}: {}".format( strftime(), WLAN().config('dhcp_hostname'), msg )
		self.console_history.put(log_line + "\n")
		
		# print to console if log level is high enough
		if log_level <= self.log_level:
			print("{}{}\u001b[0m".format( colors[log_level], log_line) )
			

	def debug(self, msg):
		# print('\u001b[36m', msg, value, "\u001b[0m" )
		self.info(msg, log_level=6)

	def error(self, msg):
		self.info(msg, log_level=0)

logger = Logger()

def info(msg):
	logger.info(msg)

def error(msg):
	logger.error(msg)

def debug(msg):
	logger.debug(msg)


