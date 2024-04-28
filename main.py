# main.py
version = (2, 0, 1)
# 2,0,1: added safeboot and flag import

import flag
from alog import espMAC, info, error, debug
import json
import uasyncio as asyncio
from machine import reset
from time import sleep

#safeboot
def sb():
	reboot(1)

def reboot(boot=0):
	flag.set('boot',boot)
	print("REBOOTING\r\n>>> ")
	if not boot:
		for i in range(10):
			print(i)
			sleep(1)
				 
	reset()
	while True:
		pass

def load_config(name=espMAC, instance="run"):
	try:
		full = {}
		with open(name) as file:
			raw = file.readline()
			while raw:
				kv = json.loads(raw)
				if instance and instance in kv:
					return kv[instance]
				full.update(kv)
				raw = file.readline()
		return full
	except:
		error("load_file: {} failed.".format(name))
		return {}

# saves file in json format, separate lines to allow for reading partial config (above)
# TODO: combine with a setup script to allow configuration via web/AP mode?

def save_json(name, content) -> bool:
	try:
		with open(name, "w") as file:
			for k,v in content.items():
				file.write(json.dumps({k:v}) )
				file.write("\n")
		info('Saved config {}'.format(name))
		return True
	except:
		error('save_file: {} failed'.format(name))
		return False

hostname = load_config()
mod = __import__(hostname)

# load_config() has at minimum a hostname to tell main.py what to import/start

def run():
	asyncio.run(mod.start(hostname))

if flag.get('boot') == 0:
	run()