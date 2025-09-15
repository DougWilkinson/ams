import machine
from time import sleep
t= machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)

def move(m,s):
	last=s.value()
	try:
		m.value(1)
		while last == s.value():
			sleep(.1)
		last = s.value()
		while last == s.value():
			sleep(.1)
	except:
		pass
	m.value(0)


tare=beans.hx.raw_read()                                                                          
while True:                                                                                       
    move(beans.dispenser.motor_pin, t)                                                            
    sleep(2)                                                                                      
    print(beans.hx.raw_read()-tare)                                                               
