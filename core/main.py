# main.py

from time import sleep, time
boot_start_seconds = time()

from versions import versions
versions[__name__[2:-2]] = 10
# 10: started new repo and refactored

import webrepl

# reboot not used here, but used in webrepl, leave it!
from system import config, espMAC, reboot, sb

from logger import info, error

import wifi

if config.boot_mode == 2:
	raise Exception("SafeBoot enabled - use reboot() to reset boot mode")

# import modules - each module should only do bare minimum when being imported
# shut off gpios, clear leds or display, etc. NO WAITING

# import main module first to prioritize setup for gpios if exists
if espMAC != config.hostname:
	info("main: loading module: {}".format(config.hostname) )
	__import__(config.hostname)

info("main: host module loaded in {} seconds".format(time() - boot_start_seconds) )	

for k, v in config.persistent.items():
	if "module_" in k and v:
		name = k.split("_")[1]
		try:
			info("main: loading module: {}".format(name) )
			mod = __import__(name)
		except Exception as e:
			error("main: Error loading module: {}: {}".format(name, e) )
			config.last_exception = e
			continue

from webconfig import app

# hass should be loaded after all other modules
# device_list has to be populated before hass
import hass

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
	try:
		info("main: starting app")
		app.run(host=host, port=port, debug=debug)
	except KeyboardInterrupt:
		app.shutdown()
		print("main: apps stopped")
	except Exception as e:
		error("main: fatal error: {}".format(e) )
		app.shutdown()

info("main: all modules loaded in {} seconds".format(time() - boot_start_seconds) )	

run()