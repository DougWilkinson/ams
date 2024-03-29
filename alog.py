# alog.py

from machine import RTC
from time import localtime, time
from network import WLAN, STA_IF
import ubinascii
from gc import mem_free
# from bootflag import flag_get, offset_time

timezone = -5

def flag_get(flag):
	return 7

def offset_time():
		return localtime(time() + ((timezone - 24) * 3600) )

w = WLAN(STA_IF)
w.active(True)

espMAC = str(ubinascii.hexlify(WLAN().config('mac')).decode() )
rtc = RTC()

# log = 0 no output,1+=error 3+=info 5+=debug
def debug(msg, value=""):
	if 6 <= flag_get('log'):
		print('\u001b[36m', msg, value, "\u001b[0m" )

def error(msg):
	info(msg, lev=0, color='\u001b[31m', end="\n")

def info(msg, lev=2, color='\u001b[0m', end="\n"):
	if lev <= flag_get('log'):
		dt = offset_time()
		print("{}{:02d}:{:02d}:{:02d}: {}: {}{}".format( color,
			dt[3], dt[4], dt[5], mem_free(), 
			msg, "\u001b[0m" ), end=end )

def started(pid):
	info("started: {}".format(pid))
def running(pid):
	info("running: {}".format(pid))
def stopped(pid):
	debug("stopped.")
def exited(pid):
	info("exited: {}".format(pid))
