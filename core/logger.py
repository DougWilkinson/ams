# logger.py

from versions import versions
versions[__name__] = 17
# 1: started to separate console and logging from settings
# 10: refactored
# 11: revised color support and cleaned up end=end
# 12: changed to non-class (also updated webconfig for debug compatibility)
# 13: added separate buffer handling for info, error and debug
# 14: combined logging to single buffer with key as log level, value as line
# 15: added exception_history
# 16: fixed exception logging to console needs lines split and fed separately
# 17: limited exception_buffer to settings["buffer_size"]

from localtime import offset_time
from network import WLAN
from sys import print_exception
from io import StringIO

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
exception_history = []
# error_history = MsgQueue(settings["buffer_size"])
# debug_history = MsgQueue(settings["buffer_size"])

def _log_msg(msg, log_level=2):
	
	# log all levels to buffer
	log_line = "{}: {}: {}".format( strftime(), WLAN().config('dhcp_hostname'), msg )
	console_history.put(str(log_level), log_line + "\n")

	# print to console if log level is high enough
	if log_level <= settings["log_level"]:
		print("{}{}\u001b[0m".format( settings["colors"][log_level], log_line) )

def info(msg):
	_log_msg(msg, log_level=2)

def debug(msg):
	# print('\u001b[36m', msg, value, "\u001b[0m" )
	_log_msg(msg, log_level=6)

def error(msg):
	_log_msg(msg, log_level=0)

def _exception(e, func_name="", count=0):
	# exception_buffer = StringIO()
	# print_exception(e, exception_buffer)
	msg = f"exception({count}): {func_name}: {e}"
	exception_history.append(f"{strftime()}: {msg}")
	if len(exception_history) > settings["buffer_size"]:
		exception_history.pop(0)
	for each_line in msg.split("\n"):
		_log_msg(each_line, log_level=0)
