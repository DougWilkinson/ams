# webconfig.py

from versions import versions
versions[__name__] = 1

# captive_portal_server.py
import os
import gc
import time
import sys
import microdot
from settings import config, get_profiles, Settings, strftime, espMAC
from settings import info as _info
from settings import error as _error
from events import config_changed
import machine

microdot.Response.default_content_type = "text/html"

class CaptivePortalServer(microdot.Microdot):
	def __init__(self, password=None):
		super().__init__()
		if password is None:
			password = config.persistent.get("device_password", "")
		self.password = password
		self.sessions = set()
		self.info("Server initialized with password length: {}".format(len(self.password)))
		self._setup_routes()

	def info(self, msg):
		_info(msg)

	def error(self, msg):
		_error(msg)

	def _html_page(self, title, body):
		return """<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
button, input[type=submit] {{ font-size: 1.1em; padding: 8px; margin-top: 10px; }}
input[type=password], input[type=text] {{ font-size: 1.1em; padding: 6px; width: 100%; }}
select {{ font-size: 1.1em; padding: 6px; width: 100%; }}
label {{ display:block; margin-top: 10px; }}
@media print {{ .pagebreak-with-line {{ page-break-after: always; }} }}
</style>
</head>
<body>
{}
</body>
</html>""".format(title, body)

	def _require_auth(self, request):
		return request.cookies.get("session") in self.sessions

	def _setup_routes(self):
		@self.route("/", methods=["GET", "POST"])
		async def login(request):
			if request.method == "POST":
				pwd = request.form.get("password", "")
				if pwd == self.password:
					token = str(id(request))
					self.sessions.add(token)
					resp = microdot.Response.redirect("/home")
					resp.set_cookie("session", token)
					self.info("Successful login from {}".format(request.client_addr))
					return resp
				else:
					self.error("Failed login attempt from {}".format(request.client_addr))
					return self._html_page("Login", "<h2>Invalid password</h2>" + self._login_form())
			return self._html_page("Login", self._login_form())


		@self.route("/home")
		async def home(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			
			# Memory stats in KB
			mem_free = gc.mem_free()
			mem_alloc = gc.mem_alloc()
			mem_total = mem_free + mem_alloc
			mem_used_kb = mem_alloc // 1024
			mem_total_kb = mem_total // 1024
			mem_used_pct = (mem_alloc * 100) // mem_total if mem_total else 0

			# Flash stats in KB
			try:
				stat = os.statvfs("/")
				flash_free = stat[0] * stat[3]
				flash_total = stat[0] * stat[2]
				flash_used = flash_total - flash_free
				flash_used_kb = flash_used // 1024
				flash_total_kb = flash_total // 1024
				flash_used_pct = (flash_used * 100) // flash_total if flash_total else 0
			except:
				flash_used_kb = flash_total_kb = flash_used_pct = 0

			# CPU Frequency in MHz
			try:
				cpu_freq = machine.freq() // 1_000_000
			except:
				cpu_freq = "N/A"

			# MicroPython version - only second value
			mp_version = ".".join([str(a) for a in sys.implementation.version])[0:-1]

			mac = espMAC

			# Uptime
			uptime_sec = time.ticks_ms() // 1000
			uptime_str = "{}d {:02}:{:02}:{:02}".format(
				uptime_sec // 86400,
				(uptime_sec % 86400) // 3600,
				(uptime_sec % 3600) // 60,
				uptime_sec % 60
			)

			# Build aligned info table
			info_rows = [
				("Current Profile", getattr(config, 'profile', 'default')),
				("MicroPython Version", mp_version),
				("Memory Used/Total", "{} KB / {} KB ({}%)".format(mem_used_kb, mem_total_kb, mem_used_pct)),
				("Flash Used/Total", "{} KB / {} KB ({}%)".format(flash_used_kb, flash_total_kb, flash_used_pct)),
				("CPU Frequency", "{} MHz".format(cpu_freq)),
				("Uptime", uptime_str),
				("Timezone", config.persistent.get("timezone", "UTC")),
				("Reboots", config.reboots)
			]

			info_html = "<table style='border-collapse:collapse;'>"
			for label, value in info_rows:
				info_html += "<tr><td style='padding:4px; font-weight:bold;'>{}:</td><td style='padding:4px;'>{}</td></tr>".format(label, value)
			info_html += "</table>"

			body = """
			<h2>{} - {}</h2>
			{}
			<div style="margin-top:15px;">
				<a href="/profiles"><button>Profiles</button></a>
				<a href="/update"><button>Update</button></a>
				<a href="/versions"><button>Versions</button></a>
				<a href="/reboot"><button>Reboot</button></a>
			</div>
			""".format(config.hostname, mac, info_html)

			self.info("Home page served to {}".format(request.client_addr))
			return self._html_page("{} - {}".format(config.hostname, mac), body)

		@self.route("/versions")
		async def versions_page(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			
			rows = "".join(
				"<tr><td>{}</td><td>{}</td></tr>".format(k, v)
				for k, v in versions.items()
			)
			body = """
			<h2>Module Versions</h2>
			<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
				<tr><th>Module</th><th>Version</th></tr>
				{}
			</table>
			""".format(rows)
			
			self.info("Versions page served to {}".format(request.client_addr))
			return self._html_page("Versions", body)


		@self.route("/profiles")
		async def profiles_page(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			profiles = get_profiles()
			current_profile = getattr(config, 'profile', None)
			options = "".join(
				"<option value='{}'{}>{}</option>".format(
					p, " selected" if p == current_profile else "", p
				) for p in profiles
			)
			body = """
			<h2>Profiles</h2>
			<select id="profileSelect">{}</select>
			<div style="display:flex;gap:10px;">
				<button onclick="editProfile()">Edit</button>
				<button onclick="deleteProfile()">Delete</button>
			</div>
			<script>
			function editProfile() {{
				let p = document.getElementById('profileSelect').value;
				if(p) window.location.href = '/edit/' + encodeURIComponent(p);
			}}
			function deleteProfile() {{
				let p = document.getElementById('profileSelect').value;
				if(p && confirm('Delete profile ' + p + '?')) {{
					fetch('/delete/' + encodeURIComponent(p), {{method:'POST'}})
					.then(() => location.reload());
				}}
			}}
			</script>
			""".format(options)
			self.info("Profiles page served to {}".format(request.client_addr))
			return self._html_page("Profiles", body)


		@self.route("/edit/<profile>")
		async def edit_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			if profile == getattr(config, 'profile', None):
				details = config.persistent
			else:
				temp_config = Settings(profile)
				details = temp_config.persistent
			fields = ""
			for k, v in details.items():
				if isinstance(v, bool):
					true_checked = " checked" if v else ""
					false_checked = " checked" if not v else ""
					fields += (
						"<label>{}:<br>"
						"<input type='radio' name='{}' value='True'{}> True "
						"<input type='radio' name='{}' value='False'{}> False"
						"</label>".format(k, k, true_checked, k, false_checked)
					)
				elif isinstance(v, list):
					value_str = ",".join(str(item) for item in v)
					input_type = "password" if k in Settings.masked_values else "text"
					fields += (
						"<label>{}:"
						"<input type='{}' name='{}' value='{}' autocapitalize='none'>"
						"</label>".format(k, input_type, k, value_str)
					)
				else:
					input_type = "password" if k in Settings.masked_values else "text"
					fields += (
						"<label>{}:"
						"<input type='{}' name='{}' value='{}' autocapitalize='none'>"
						"</label>".format(k, input_type, k, v)
					)
			
			# Add "New Profile Name" field
			fields += (
				"<label>New Profile Name:"
				"<input type='text' name='_new_profile' value='' autocapitalize='none'>"
				"</label>"
			)

			body = """
			<h2>Edit {}</h2>
			<form method="POST" action="/update/{}">
				{}
				<div style="margin-top:10px;">
					<input type="submit" name="_action" value="Update">
					<input type="submit" name="_action" value="Set as Default">
				</div>
			</form>
			""".format(profile, profile, fields)
			self.info("Edit page for profile '{}' served to {}".format(profile, request.client_addr))
			return self._html_page("Edit {}".format(profile), body)


		# @self.route("/edit/<profile>")
		# async def edit_profile(request, profile):
		# 	field_order = [ "wifi_ssid", "wifi_secret", "", "ha_topic", "ha_config", "mqtt_server", "mqtt_ssl", "mqtt_username", "mqtt_password", "", "timezone", "ntp_servers", "ntp_interval" ]
		# 	if not self._require_auth(request):
		# 		return microdot.Response.redirect("/")
		# 	if profile == getattr(config, 'profile', None):
		# 		details = config.persistent
		# 	else:
		# 		temp_config = Settings(profile)
		# 		details = temp_config.persistent
		# 	fields = ""
		# 	for field_name in field_order:
		# 		if not field_name:
		# 			fields += "<hr style='border: 2px solid black; margin-top: 20px; margin-bottom: 20px;'>"
		# 			continue
		# 		if field_name not in details:
		# 			continue
		# 		k = field_name
		# 		v = details[k]
		# 		# Boolean values -> radio buttons
		# 		if isinstance(v, bool):
		# 			true_checked = " checked" if v else ""
		# 			false_checked = " checked" if not v else ""
		# 			fields += (
		# 				"<label>{}:<br>"
		# 				"<input type='radio' name='{}' value='True'{}> True "
		# 				"<input type='radio' name='{}' value='False'{}> False"
		# 				"</label>".format(k, k, true_checked, k, false_checked)
		# 			)
		# 		# Lists -> comma-separated string
		# 		elif isinstance(v, list):
		# 			value_str = ",".join(str(item) for item in v)
		# 			input_type = "password" if k in Settings.masked_values else "text"
		# 			fields += (
		# 				"<label>{}:"
		# 				"<input type='{}' name='{}' value='{}' autocapitalize='none'>"
		# 				"</label>".format(k, input_type, k, value_str)
		# 			)
		# 		# Everything else -> normal input
		# 		else:
		# 			input_type = "password" if k in Settings.masked_values else "text"
		# 			fields += (
		# 				"<label>{}:"
		# 				"<input type='{}' name='{}' value='{}' autocapitalize='none'>"
		# 				"</label>".format(k, input_type, k, v)
		# 			)
		# 	body = """
		# 	<h2>Profile: {}</h2>
		# 	<form method="POST" action="/update/{}">
		# 		{}
		# 		<input type="submit" value="Set as Default">
		# 	</form>
		# 	""".format(profile, profile, fields)
		# 	self.info("Edit page for profile '{}' served to {}".format(profile, request.client_addr))
		# 	return self._html_page("Edit {}".format(profile), body)


		@self.route("/update/<profile>", methods=["POST"])
		async def update_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			new_profile_name = request.form.get("_new_profile", "").strip()
			self.info("new_profile_name: {}".format(new_profile_name) )
			
			action = request.form.get("_action", "Update")
			self.info("action: {}".format(action) )

			if profile == getattr(config, 'profile', None):
				target_config = config
			else:
				target_config = Settings(profile)

			# Update fields from form
			for k, v in request.form.items():
				
				# v is returned as a list of one item for some reason (str)
				v = v[0]

				if k.startswith("_"):  # skip special form fields
					continue
				orig_val = target_config.persistent.get(k)

				#print("updating values: key: {}, orig_val: {}, new_val: {}".format(k, orig_val, v))
				
				if isinstance(orig_val, bool):
					target_config.persistent[k] = True if v == "True" else False
				elif isinstance(orig_val, list):
					target_config.persistent[k] = [item.strip() for item in v.split(",") if item.strip()]
				else:
					target_config.persistent[k] = v

			#print("updated_target_config_persistent: ", target_config.persistent)
			#print("updated_target_config_saved.raw_state: ", target_config.saved.raw_state)
			
			target_config.save()
			self.info("Profile '{}' updated".format(profile))
			config_changed.set()

			# Handle "Set as Default" action
			if action == "Set as Default":
				if new_profile_name:
					new_cfg = Settings(new_profile_name)
					new_cfg.persistent.update(target_config.persistent)
					new_cfg.save()
					config.set_as_default(new_profile_name)
					self.info("New profile '{}' created and set as default".format(new_profile_name))
				else:
					config.set_as_default(profile)
					self.info("Profile '{}' set as default".format(profile))

			return microdot.Response.redirect("/profiles")


		# @self.route("/update/<profile>", methods=["POST"])
		# async def update_profile(request, profile):
		# 	if not self._require_auth(request):
		# 		return microdot.Response.redirect("/")
		# 	if profile == getattr(config, 'profile', None):
		# 		target_config = config
		# 	else:
		# 		target_config = Settings(profile)
			
		# 	for k, v in request.form.items():
		# 		orig_val = target_config.persistent.get(k)
		# 		# Convert strings back to original type
		# 		if isinstance(orig_val, bool):
		# 			if type(v) is str:
		# 				target_config.persistent[k] = True if v == "True" else False
		# 			else:
		# 				target_config.persistent[k] = v
		# 		elif isinstance(orig_val, list):
		# 			print(v, orig_val, request.form)
		# 			if type(v) is str:
		# 				target_config.persistent[k] = [item.strip() for item in v.split(",") if item.strip()]
		# 			else:
		# 				target_config.persistent[k] = v
		# 		else:
		# 			target_config.persistent[k] = v
			
		# 	target_config.save()
		# 	self.info("Profile '{}' updated".format(profile))
		# 	if profile != getattr(config, 'profile', None):
		# 		config.set_as_default(profile)
		# 		self.info("Profile '{}' set as default".format(profile))
		# 	return microdot.Response.redirect("/profiles")

		@self.route("/delete/<profile>", methods=["POST"])
		async def delete_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			fname = "sensor.profile.{}".format(profile)
			if fname in os.listdir():
				try:
					os.remove(fname)
					self.info("Profile '{}' deleted".format(profile))
				except Exception as e:
					self.error("Failed to delete profile '{}': {}".format(profile, e))
			return "OK"

		@self.route("/reboot")
		async def reboot_page(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			from settings import reboot
			self.info("Reboot requested by {}".format(request.client_addr))
			reboot()
			return self._html_page("Reboot", "<h2>Rebooting...</h2>")

		# Captive portal triggers
		@self.route("/generate_204")
		@self.route("/hotspot-detect.html")
		@self.route("/ncsi.txt")
		@self.route("/fwlink")
		async def captive_redirect(request):
			self.info("Captive portal redirect from {}".format(request.client_addr))
			return microdot.Response.redirect("/")

	def _login_form(self):
		return """
		<h2>Please Login</h2>
		<form method="POST">
			<input type="password" name="password" placeholder="Password" autocapitalize="none">
			<input type="submit" value="Login">
		</form>
		"""


# Instantiate for external startup
app = CaptivePortalServer()
