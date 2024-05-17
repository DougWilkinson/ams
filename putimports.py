# putimports.py
# look for imports and create a list of files to copy

from sys import argv

#skip = ("#", "dht", "uasyncio", "neopixel", "machine", "alog", "time", "network", "ubinascii", "gc", "flag", "json", "hass", "msgqueue", "device")
skip = ("#", "umqtt.simple", "dht", "uasyncio", "neopixel", "machine", "time", "network", "ubinascii", "gc", "json")
found = []

def find_imports(filename):
	try:
		with open(filename) as file:
			line = file.readline()
			while line:
				if "import" in line or "from" in line:
					items = line.strip().split(" ")
					if (items[1] not in skip and "#" not in items[0]):
						if items[0] == "from" or items[0] == "import":
							nextfile = items[1] + ".py"
							if nextfile not in found:
								print(nextfile)
								find_imports(nextfile)
								found.append(nextfile)
					# else:
					# 	print('{} : items[1] "{}" in skip? {}'.format(filename, items[1], items[1] in skip) )
				line = file.readline()
	except FileNotFoundError:
		pass

for file in argv[1:]:
	find_imports(file)