# webconfig.py

from versions import versions
versions[__name__] = 1

# captive_portal_server.py
import os
import gc
import time
import sys
import microdot
from settings import config, get_profiles, Settings, strftime, espMAC, field_display
from settings import info as _info
from settings import error as _error
from events import config_changed
import machine

import hashlib
import binascii

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

	def _sanitize_filename(self, name):
		"""Return a safe, flat filename; disallow path traversal and absolute paths."""
		# Strip directory components and reject suspicious names
		name = str(name or "").strip()
		# remove any leading slashes
		while name.startswith("/"):
			name = name[1:]
		# collapse traversal
		if ".." in name or "/" in name or "\\" in name or name == "":
			raise ValueError("Invalid filename")
		return name

	def _sha256_bytes_of_data(self, data_bytes):
		"""Return SHA-256 digest (bytes) of a bytes-like object."""
		h = hashlib.sha256()
		# MicroPython can handle big updates; still keep it simple
		h.update(data_bytes)
		return h.digest()

	def _sha256_bytes_of_file(self, path, chunk_size=4096):
		"""Return SHA-256 digest (bytes) of a file, or None if file doesn't exist."""
		try:
			st = os.stat(path)
		except:
			return None
		h = hashlib.sha256()
		try:
			with open(path, "rb") as f:
				while True:
					chunk = f.read(chunk_size)
					if not chunk:
						break
					h.update(chunk)
			return h.digest()
		except:
			return None

	def _digest_to_hex(self, digest_bytes):
		"""Hex string for logging/UX (not stored)."""
		return binascii.hexlify(digest_bytes).decode("ascii")


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

			for name, section in field_display.items():
				for field in section:
					if field in details:
						k = field
						v = details[field]
						

						# for k, v in details.items():
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

				# add a horizontal line after each section
				fields += "<hr style='margin:15px 0;'>"

			# Add "New Profile Name" field
			fields += (
				"<label>New Profile Name:"
				"<input type='text' name='_new_profile' value='' autocapitalize='none'>"
				"</label>"
			)

			body = """
			<h2>Edit profile: {}</h2>
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
				elif isinstance(orig_val, int):
					target_config.persistent[k] = int(v)
				else:
					target_config.persistent[k] = v

			#print("updated_target_config_persistent: ", target_config.persistent)
			#print("updated_target_config_saved.raw_state: ", target_config.saved.raw_state)
			
			target_config.save()
			self.info("Profile updated: {}".format(profile))
			config_changed.set()

			# TODO: Change so that when a new profile name is specified try to save the current profile as that new profile
			#       If update button pressed, just update, if set as default is pressed, make it the default too
			#
			#

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

		@self.route("/delete/<profile>", methods=["POST"])
		async def delete_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			if profile == espMAC:
				profile_to_delete = config
			else:
				profile_to_delete = Settings(profile)

			if profile_to_delete.delete():
				self.info("Profile '{}' deleted".format(profile))
				return "OK"
			else:
				self.info("Profile '{}' not deleted".format(profile))
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

		@self.route("/upload/<filename>", methods=["GET", "POST"])
		async def upload_file(request, filename):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			# Basic HTML helper for responses
			def result_page(title, msg_html):
				return self._html_page(title, "<h2>{}</h2><div>{}</div>".format(title, msg_html))

			if request.method == "GET":
				# Minimal upload UI that sends RAW bytes (not multipart)
				safe_name = ""
				try:
					safe_name = self._sanitize_filename(filename)
				except Exception as e:
					return result_page("Upload Error", "Invalid filename: {}".format(e))

				body = """
				<h2>Upload File: {fname}</h2>
				<p>This form sends the file as raw bytes to <code>/upload/{fname}</code>. Works for .py and .mpy.</p>
				<input type="file" id="file" />
				<button id="send">Upload</button>
				<pre id="out" style="white-space:pre-wrap;background:#f5f5f5;padding:8px;"></pre>
				<script>
				const btn = document.getElementById('send');
				const out = document.getElementById('out');
				btn.onclick = async () => {{
					const f = document.getElementById('file').files[0];
					if (!f) {{ out.textContent = "Choose a file first."; return; }}
					try {{
						const buf = await f.arrayBuffer();
						const resp = await fetch("/upload/{fname}", {{
							method: "POST",
							headers: {{"Content-Type":"application/octet-stream"}},
							body: buf
						}});
						out.textContent = await resp.text();
					}} catch (e) {{
						out.textContent = "Upload failed: " + e;
					}}
				}};
				</script>
				""".format(fname=safe_name)
				return self._html_page("Upload {}".format(safe_name), body)

			# POST path: accept raw bytes and write if different
			try:
				safe_name = self._sanitize_filename(filename)
			except Exception as e:
				self.error("Upload rejected (bad filename '{}'): {}".format(filename, e))
				return result_page("Upload Error", "Invalid filename: {}".format(e))

			# Read raw request body (should be bytes)
			data = request.body
			if data is None:
				# Some microdot builds might expose .body as None with small posts; try .stream.read()
				try:
					data = request.stream.read()
				except:
					data = None

			if not data:
				return result_page("Upload Error", "No data received. Send raw bytes (Content-Type: application/octet-stream).")

			# Compute incoming hash
			in_digest = self._sha256_bytes_of_data(data)
			in_hex = self._digest_to_hex(in_digest)

			# Compare with existing file if present
			existing_digest = self._sha256_bytes_of_file(safe_name)
			if existing_digest is not None and existing_digest == in_digest:
				self.info("Upload skipped: '{}' unchanged (sha256={})".format(safe_name, in_hex[:16] + "..."))
				# Return SHA-256 as plain text
				return microdot.Response(self._digest_to_hex(existing_digest), content_type="text/plain")

			# Write atomically via temp file then rename
			tmp_name = safe_name + ".tmp"
			try:
				with open(tmp_name, "wb") as f:
					f.write(data)
					f.flush()
				# Remove existing target if present to avoid rename errors on some FS
				try:
					os.remove(safe_name)
				except:
					pass
				os.rename(tmp_name, safe_name)
			except Exception as e:
				# cleanup temp
				try:
					os.remove(tmp_name)
				except:
					pass
				self.error("Upload failed for '{}': {}".format(safe_name, e))
				return microdot.Response("Failed to write file: {}".format(e), status_code=500)

			# Optional: free RAM after big upload
			try:
				del data
				gc.collect()
			except:
				pass

			self.info("Uploaded '{}' (sha256={})".format(safe_name, in_hex[:16] + "..."))
			# Return SHA-256 of the newly written file
			return microdot.Response(in_hex, content_type="text/plain")

		@self.route("/sha256/<filename>")
		async def sha256_query(request, filename):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			try:
				safe_name = self._sanitize_filename(filename)
			except Exception as e:
				return microdot.Response("Invalid filename", status_code=400)

			digest = self._sha256_bytes_of_file(safe_name)
			if digest is None:
				return microdot.Response("File not found", status_code=404)

			hexval = self._digest_to_hex(digest)
			self.info("SHA256({}) = {}".format(safe_name, hexval))

			# Plain text output
			return microdot.Response(hexval)

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
