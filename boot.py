# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#fakeimport webrepl_cfg.py
import webrepl
webrepl.start()
