# ntpd.py

import socket
import time
import asyncio

# NTP server settings
NTP_PORT = 123
NTP_VERSION = 3


class NTPServer:
	def __init__(self):
	# Create a UDP socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(('', NTP_PORT))

		print(f"NTP server listening on port {NTP_PORT}...")

		while True:
			try:
				data, address = sock.recvfrom(1024)
				if data:
					client = ntplib.NTPClient()
					response = client.request('0.pool.ntp.org', version=NTP_VERSION)
					sock.sendto(response.to_data(), address)
			except Exception as e:
				print(f"Error: {e}")

