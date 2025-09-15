


import network, time

def wifi_reset():
	sta = network.WLAN(network.STA_IF)	
	sta.active(False)
	ap = network.WLAN(network.AP_IF)
	ap.active(False)
	sta.active(True)
	while not sta.active():
		time.sleep(0.1)
	sta.disconnect()   # For ESP8266
	while sta.isconnected():
		time.sleep(0.1)
	return sta, ap


import network
import espnow



def watch():
	while True:
		host, msg = e.recv()
		if msg:             # msg == None if timeout in recv()
			print(host, msg)
			if msg == b'end':
				break

sta, ap = wifi_reset()

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()   # Because ESP8266 auto-connects to last Access Point

e = espnow.ESPNow()
e.active(True)


########## SEND TO PEER

import network
import espnow

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
sta.active(True)
sta.disconnect()      # For ESP8266

e = espnow.ESPNow()
e.active(True)
peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'   # MAC address of peer's wifi interface
e.add_peer(peer)      # Must add_peer() before send()

def send():	
	e.send(peer, "Starting...")
	for i in range(100):
		e.send(peer, str(i)*20, True)
	e.send(peer, b'end')



#esp32 ap mac 
e.add_peer(b'\xd8;\xda\xa2\xd5,')

# adding peer with mac [, lmk][, channel][, ifidx][, encrypt], 
e.add_peer(b"j\xc6:\xea\x17'", False, 11, 0, False)

# esp32
# >>> ap.config('mac')
# b'\xd8;\xda\xa2\xd5,'
# >>> sta.con
# config          connect
# >>> sta.config('mac')
# b'\xd8;\xda\xa2\xd5-'
