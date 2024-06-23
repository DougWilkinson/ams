# flag.py

version = (2, 0, 2)
# 202: added minutes/hours to track time updated

from machine import RTC
from time import localtime, time

rtc = RTC()
names = ["checksum","magic","length","log","timezone", "boot", "timesynced"]
values = []

def set(flag=None, value=1) -> None:
	if flag:
		values[names.index(flag)] = value
		values[0] = sum(values[1:]) & 255
		rtc.memory(bytes(values))
	return

def show():
	line = "Bootvalues: "
	for i in names:
		line += "{}={} ".format(i,get(i))
	print(line)

def clear(flag):
	if flag in names:
		set(flag, value=0)

def get(flag) -> int:
	return values[names.index(flag)]

for flag in rtc.memory():
	values.append(flag)

if len(values) > 3 and values[1] == 52 and len(names) == values[2] and sum(values[1:]) % 255 == values[0]:
	print("flag: Using RTC values:")
else:
	print("flag: Initializing RTC values:")
	values = [0,52,len(names)] + [0]*(len(names)-3)
	set('log',7)
	set('timezone',19)

show()