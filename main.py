# main.py

from alog import espMAC, info, error, debug, offset_time
import json
import asyncio

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

mod = __import__(load_config())

def run():
	asyncio.run(mod.start())

run()