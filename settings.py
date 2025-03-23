# save_json.py
# saves file in json format, separate lines to allow for reading partial config (above)
# TODO: combine with a setup script to allow configuration via web/AP mode?

from json import dumps
from core import info, error

def save_json(filename, content) -> bool:
	try:
		with open(filename, "w") as file:
			for k,v in content.items():
				file.write(dumps({k:v}) )
				file.write("\n")
		info('Saved config {}'.format(filename))
		return True
	except:
		error('save_file: {} failed'.format(filename))
		return False
