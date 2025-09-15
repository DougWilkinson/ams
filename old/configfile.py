# loadconfig.py

from json import loads
def load_config(name, key="run"):
	try:
		full = {}
		with open(name) as file:
			raw = file.readline()
			while raw:
				kv = loads(raw)
				if key and key in kv:
					return kv[key]
				full.update(kv)
				raw = file.readline()
		return full
	except:
		error("load_file: {} failed.".format(name))
		return {}

