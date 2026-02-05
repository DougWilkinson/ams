# main.py

from time import sleep, time
boot_start_seconds = time()

from versions import versions
versions["main"] = 14
# 10: started new repo and refactored
# 11: added mpy_exception
# 12: changed mpy_exception to use error()
# 13: changed to homeassistant (was hass)
# 14: added _exception support for importing hostname module
import webrepl

# reboot not used here, but used in webrepl, leave it!
from system import config, espMAC, reboot, sb
from sys import print_exception
from io import StringIO
from logger import info, error, _exception

import wifi

if config.boot_mode == 2:
	raise Exception("SafeBoot enabled - use reboot() to reset boot mode")

# import modules - each module should only do bare minimum when being imported
# shut off gpios, clear leds or display, etc. NO WAITING

# import main module first to prioritize setup for gpios if exists
if espMAC != config.hostname:
	try:
		info("main: loading module: {}".format(config.hostname) )
		__import__(config.hostname)
		info("main: host module loaded in {} seconds".format(time() - boot_start_seconds) )	
	except Exception as e:
		exception_buffer = StringIO()
		print_exception(e, exception_buffer)
		_exception(exception_buffer.getvalue(), f"main_import: {config.hostname}")

# for k, v in config.persistent.items():
# 	if "module_" in k and v:
# 		name = k.split("_")[1]
# 		try:
# 			info("main: loading module: {}".format(name) )
# 			mod = __import__(name)
# 		except Exception as e:
# 			error("main: loading module: {} exception: {}".format(name, e) )
# 			continue

from webconfig import app

# hass should be loaded after all other modules

try:
	import homeassistant
except Exception as e:
	error("main: error importing homeassistant: {}".format(e) )

# 2 = safeboot, do not start named module
# 3 = delay start to allow remote console time

	
# wait for netrepl to connect or 20 seconds
if config.boot_mode == 3:
	delay = 20
	while delay > 0 and webrepl.client_s is None:
		sleep(1)
		delay -= 1

# Only count reboots if power on or unexpected
if config.boot_mode == 0:
	config.reboots += 1

# boot mode 0 = power on or unexpected reboot
# set here for next potential unexpected reboot
# all other restarts are done through reboot() function
config.boot_mode = 0


def run(host="0.0.0.0", port=80, debug=True):
	while True:
		try:
			info("main: starting app")
			app.run(host=host, port=port, debug=debug)
		except KeyboardInterrupt:
			print("main: run: keyboard interrupt")
			app.shutdown()
			print("main: apps stopped")
			return
		except Exception as e:
			error("main: run: exception error: {} - reloading app".format(e))
			sleep(1)

info("main: all modules loaded in {} seconds".format(time() - boot_start_seconds) )	

run()