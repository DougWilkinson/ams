# logger.py

from versions import versions
versions[__name__] = 12
# 1: started to separate console and logging from settings
# 10: refactored
# 11: revised color support and cleaned up end=end
# 12: changed to non-class (also updated webconfig for debug compatibility)

from localtime import offset_time
from network import WLAN
from sys import print_exception

from msgqueue import MsgQueue

# errors 0-1: red
# info 2-5: white
# debug 6-7: cyan
settings = {"colors": ["\u001b[31m", "\u001b[31m", "\u001b[0m", "\u001b[0m", "\u001b[0m", "\u001b[0m", "\u001b[36m", "\u001b[36m"],
			"log_level": 7, "buffer_size": 100}

def strftime():
	month, day, year, hour, minute, second, _, _ = offset_time()
	return "{:02d}/{:02d}/{:02d}-T{:02d}:{:02d}:{:02d}".format( month, day, year, hour, minute, second )

console_history = MsgQueue(settings["buffer_size"])
debug_history = MsgQueue(settings["buffer_size"])

def info(msg, log_level=2):
	
	# log all levels to buffer
	log_line = "{}: {}: {}".format( strftime(), WLAN().config('dhcp_hostname'), msg )
	console_history.put(log_line + "\n")
	
	# print to console if log level is high enough
	if log_level <= settings["log_level"]:
		print("{}{}\u001b[0m".format( settings["colors"][log_level], log_line) )
			
def debug(msg):
	# print('\u001b[36m', msg, value, "\u001b[0m" )
	info(msg, log_level=6)

def error(msg):
	info(msg, log_level=0)

def mpy_exception(msg, e):
	info(msg, log_level=0)
	info(print_exception(e), log_level=0)

