# logger.py

from versions import versions
versions[__name__] = 1
# 1: started to separate console and logging from settings

from localtime import offset_time
from network import WLAN

from msgqueue import MsgQueue

def strftime():
	month, day, year, hour, minute, second, _, _ = offset_time()
	return "{:02d}/{:02d}/{:02d}-T{:02d}:{:02d}:{:02d}".format( month, day, year, hour, minute, second )

class Logger:
	def __init__(self, log_level=7, buffer_size=100):
		self.log_level = log_level
		self.console_history = MsgQueue(100)

	def info(self, msg, log_level=2, color='\u001b[0m', end="\n"):
	
		# log all levels to buffer
		log_line = "{}: {}: {}".format( strftime(), WLAN().config('dhcp_hostname'), msg )
		self.console_history.put(log_line + "\n")
		
		# print to console if log level is high enough
		if log_level <= self.log_level:
			print("{}{}\u001b[0m".format( color, log_line, end=end) )
			

	def debug(self, msg):
		if 6 <= self.log_level:
			# print('\u001b[36m', msg, value, "\u001b[0m" )
			self.info(msg, log_level=6, color='\u001b[36m')

	def error(self, msg):
		self.info(msg, log_level=0, color='\u001b[31m')

logger = Logger()

def info(msg):
	logger.info(msg)

def error(msg):
	logger.error(msg)

def debug(msg):
	logger.debug(msg)


