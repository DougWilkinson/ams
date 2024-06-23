#natives.py

@micropython.native
def toggle(p):
	p.value(1)
	p.value(0)
