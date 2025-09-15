# wifihistory.py

from ouilookup import OuiLookup

olook = OuiLookup()

ids = {}

with open("wifieast.console", "r") as f:
	last_day = 0
	last_hour = "00"
	starT_found = False
	histogram_tracking = ""

	for line in f:

		if "ssid" in line or ("new:" not in line and "expired:" not in line):
			continue
		fields = line.split()
		if "db" in fields[11] or "b" not in fields[11]:
			continue
		#print(fields[0], fields[3], fields[4], fields[11    ])
		hour = fields[0][4:6]
		
		db = int(fields[8])

		if not starT_found:
			if hour == "00":
				starT_found = True
		
		if starT_found and last_hour != hour:
			histogram_tracking += "."
			last_hour = hour
			for id, details in ids.items():
				if details["state"] == "on":
					new = details["new"]
					char = str(new) if new < 10 else "#"
					details["history"] += char
				else:
					details["history"] += "."

		action = fields[3]
		channel = fields[6]
		bssid = fields[4][2:-1].upper()
		result = olook.query(bssid)[0]
		#print(bssid, result)
		if bssid in result and result[bssid] is not None:
			bssid = result[bssid][0:6] + bssid[6:]

		if len(fields) > 12:
			ssid = ""
			parts = fields[11:]
			for part in parts:
				ssid += part + " "
			ssid = ssid[:-1]
		else:
			ssid = fields[11]

		id = bssid + ":" + ssid[2:-5] + ":" + channel
		#print(time_stamp, action, bssid, ssid )
		
		if id not in ids:
			ids[id] = {"new": 1, "expired": 0, "db_values" : [db], "channel": int(channel), "history": histogram_tracking}

		if "new:" in line:
			if starT_found:
				ids[id]["new"] += 1
			ids[id]["state"] = "on"
			ids[id]["db_values"].append(db)
		
		if "expired:" in line:
			if starT_found:
				ids[id]["expired"] += 1
			ids[id]["state"] = "off"

	for channel in range(1, 13):
		first = True
		for id, details in ids.items():
			#print( "{:40s} - new:{:3d} - expired:{:3d}".format(id, details["new"], details["expired"] ) )
			average = int(sum(details["db_values"]) / len(details["db_values"]) )
			if details["channel"] == channel and average > -80:
				if first:
					first = False
					print("{:45s} {:3s}".format("CHANNEL: "+str(channel), "          11111111112222"))
					print("{:45s} {:3s} : {:4s}".format("ID", "012345678901234567890123", "dbAvg"))
				print( "{:45s} {:24s} : {:4d}".format(id, details["history"], average ) )
		
		print("")