# webconfig.py

from versions import versions
versions[__name__] = 17
# 2: supported profiles and logger split
# 12: changed logger to non-class
# 13: log_level added to tail_console (future url support log level filtering)
# 14: modified tail_console to handle exceptions better
# 15: added exception_history to tail_console
# 16: added tail_console exception handling
# 17: added check for line length in tail_console - truncate if too long

import os
import gc
import time
import sys
import microdot
from sse import with_sse
from system import config, reboot
from profiles import Profile, get_profiles, profile_field_display, espMAC, delete_profile
import logger
from events import config_changed
import machine
import asyncio
from io import StringIO

import hashlib
import binascii

microdot.Response.default_content_type = "text/html"

class CaptivePortalServer(microdot.Microdot):
	def __init__(self):
		super().__init__()
		self.sessions = set()
		self._setup_routes()
		self.profile_result_message = None

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
				if pwd == config.password:
					token = str(id(request))
					self.sessions.add(token)
					resp = microdot.Response.redirect("/home")
					resp.set_cookie("session", token)
					logger.info("Successful login from {}".format(request.client_addr))
					return resp
				else:
					logger.error("Failed login attempt from {}".format(request.client_addr))
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
				("Hostname", config.hostname),
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

			logger.info("Home page served to {}".format(request.client_addr))
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
			
			logger.info("Versions page served to {}".format(request.client_addr))
			return self._html_page("Versions", body)


		@self.route("/profiles")
		async def profiles_page(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			
			# get a list of all saved profiles (not including default)
			profiles = get_profiles()
			options = "".join(
				"<option value='{}'{}>{}</option>".format(
					p, " selected" if p == espMAC else "", p
				) for p in profiles
			)

			show_message = ""

			if self.profile_result_message:
				show_message = """
				<div style="margin-top:15px;">
				<p class="notice"></p>
				</div>
				"""

			body = """
			<h2>Profiles</h2>
			<select id="profileSelect">{}</select>
			<div style="display:flex;gap:10px;">
				<button onclick="editProfile()">Edit</button>
				<button onclick="deleteProfile()">Delete</button>
				<button onclick="loadProfile()">Load</button>
				<button onclick="saveAs()">Save As...</button>
			</div>
			{}
			<script>
			function saveAs() {{
				const name = prompt('Enter a new profile name:');
				if (name && name.trim() !== '') {{
				fetch('/save_profile_as', {{
					method: 'POST',
					headers: {{ 'Content-Type': 'application/json' }},
					body: JSON.stringify({{ 'new_name': name.trim() }})
				}})
				.then(response => response.text())
				.then(text => alert(text))
				.catch(err => alert('Error: ' + err));
				}}
			}}
			function editProfile() {{
				let p = document.getElementById('profileSelect').value;
				if(p) window.location.href = '/edit/' + encodeURIComponent(p);
			}}
			function loadProfile() {{
				let p = document.getElementById('profileSelect').value;
				if(p) window.location.href = '/load/' + encodeURIComponent(p);
			}}
			function deleteProfile() {{
				let p = document.getElementById('profileSelect').value;
				if (p) {{
					let msg = "Delete profile " + p + "?";
					if (confirm(msg)) {{
						fetch('/delete/' + encodeURIComponent(p), {{method:'POST'}})
						.then(() => location.reload());
					}}
				}}
			}}
			</script>
			""".format(options, show_message)
			self.profile_result_message = None
			logger.info("Profiles page served to {}".format(request.client_addr))
			return self._html_page("Profiles", body)

		@self.route('/save_profile_as', methods=['POST'])
		async def save_profile_as(request):
			if not self._require_auth(request):
				return microdot.Response('Unauthorized', status_code=401)

			try:
				data = request.json
				new_name = data.get('new_name', '').strip()
				if not new_name:
					return microdot.Response('Invalid name', status_code=400)

				if config.save_as(new_name):
					self.profile_result_message = "Profile saved as {}".format(new_name)
				else:
					self.profile_result_message = "Invalid name or error saving profile"
			except Exception as e:
				self.profile_result_message = "Error saving profile"

			return microdot.Response.redirect("/profiles")

		@self.route("/load/<profile>")
		async def load_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			# Already checked for trying to set default as active above
			# go ahead and set the selected one
						
			logger.info("Loading profile: {}".format(profile))

			load_success = config.load(profile)
			
			if load_success:
				return microdot.Response.redirect("/reboot")
			else:
				self.profile_result_message = "Load profile failed - configuration may be invalid"
				return microdot.Response.redirect("/profiles")

			return microdot.Response.redirect("/")


		@self.route("/edit/<profile>")
		async def edit_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")
			
			details = config.persistent

			fields = ""

			for name, section in profile_field_display.items():
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
							input_type = "password" if k in Profile.masked_values else "text"
							fields += (
								"<label>{}:"
								"<input type='{}' name='{}' value='{}' autocapitalize='none'>"
								"</label>".format(k, input_type, k, value_str)
							)
						else:
							input_type = "password" if k in Profile.masked_values else "text"
							fields += (
								"<label>{}:"
								"<input type='{}' name='{}' value='{}' autocapitalize='none'>"
								"</label>".format(k, input_type, k, v)
							)

				# add a horizontal line after each section
				fields += "<hr style='margin:15px 0;'>"

			# Add "New Profile Name" field
			# fields += (
			# 	"<label>New Profile Name:"
			# 	"<input type='text' name='_new_profile' value='' autocapitalize='none'>"
			# 	"</label>"
			# )

			body = """
			<h2>Edit profile: {}</h2>
			<form method="POST" action="/update/{}">
				{}
				<div style="margin-top:10px;">
					<input type="submit" name="_action" value="Save">
					<input type="submit" name="_action" value="Cancel">
				</div>
			</form>
			""".format(profile, profile, fields)
			logger.info("Edit page for profile '{}' served to {}".format(profile, request.client_addr))
			return self._html_page("Edit {}".format(profile), body)


		@self.route("/update/<profile>", methods=["POST"])
		async def update_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			# new_profile_name = request.form.get("_new_profile", "").strip().lower()

			action = request.form.get("_action", "Cancel")
			logger.info("action: {}".format(action) )

			if action == "Cancel":
				return microdot.Response.redirect("/profiles")
			
			# if new_profile_name:
			# 	logger.info("new_profile_name: {}".format(new_profile_name) )

			# set to true later if one of the settings changed to avoid unnecessary saves
			something_changed = False

			# Update fields from form
			for k, v in request.form.items():
				
				# v is returned as a list of one item for some reason (str)
				v = v[0]

				if k.startswith("_"):  # skip special form fields
					continue
				orig_val = config.persistent.get(k)

				#print("updating values: key: {}, orig_val: {}, new_val: {}".format(k, orig_val, v))
				
				if isinstance(orig_val, bool):
					config.persistent[k] = True if v == "True" else False
				elif isinstance(orig_val, list):
					config.persistent[k] = [item.strip() for item in v.split(",") if item.strip()]
				elif isinstance(orig_val, int):
					config.persistent[k] = int(v)
				else:
					config.persistent[k] = v

				if orig_val != config.persistent[k]:
					something_changed = True

			#print("updated_target_config_persistent: ", config.persistent)
			#print("updated_target_config_saved.raw_state: ", config.saved.raw_state)
			
			if something_changed:
				config.save()
				logger.info("Profile updated: {}".format(profile))
				
				# notify other modules that the config has changed
				config_changed.set()

			return microdot.Response.redirect("/home")

		@self.route("/delete/<profile>", methods=["POST"])
		async def delete_profile(request, profile):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			delete_profile(profile)
			
			if profile == espMAC:
				return microdot.Response.redirect("/reboot")
			else:
				return microdot.Response.redirect("/profiles")

		@self.route("/reboot")
		async def reboot_page(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			# Reboot countdown page
			body = """
			<h2>Rebooting...</h2>
			<p>Device will reboot in <span id="countdown">10</span> seconds.</p>
			<script>
			let counter = 10;
			let timer = setInterval(function() {
				counter--;
				document.getElementById('countdown').innerText = counter;
				if (counter <= 0) {
					clearInterval(timer);
					window.location.href = "/";
				}
			}, 1000);
			</script>
			"""

			# Schedule actual device reboot after response is sent
			async def do_reboot():
				await asyncio.sleep(1)  # let page flush to client
				reboot(0)

			asyncio.create_task(do_reboot())

			return self._html_page("Reboot", body)


		# Captive portal triggers
		@self.route("/generate_204")
		@self.route("/hotspot-detect.html")
		@self.route("/ncsi.txt")
		@self.route("/fwlink")
		async def captive_redirect(request):
			logger.info("Captive portal redirect from {}".format(request.client_addr))
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
				logger.error("Upload rejected (bad filename '{}'): {}".format(filename, e))
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
				logger.info("Upload skipped: '{}' unchanged (sha256={})".format( safe_name, in_hex[:16] + "..." ))

				return microdot.Response(self._digest_to_hex(existing_digest),
										headers={"Content-Type": "text/plain"})

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
				logger.error("Upload failed for '{}': {}".format(safe_name, e))
				return microdot.Response("Failed to write file: {}".format(e), status_code=500)

			# Optional: free RAM after big upload
			try:
				del data
				gc.collect()
			except:
				pass

			logger.info("Uploaded '{}' (sha256={})".format(safe_name, in_hex[:16] + "..."))
			return microdot.Response(in_hex, headers={"Content-Type": "text/plain"})

		@self.route("/cleanup_files", methods=["POST"])
		async def cleanup_files(request):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			print(request.json)
			f = "before file loop"
			try:
				# Accept JSON list or form-encoded string
				if request.headers.get("Content-Type") == "application/json":
					filenames = request.json['imported_files']
				else:
					raw = request.form.get("filenames", "")
					filenames = [f.strip() for f in raw.split(",") if f.strip()]

				if not isinstance(filenames, list):
					return microdot.Response("Cleanup Files Error: Invalid input format", 
							  status_code=400, headers={"Content-Type": "text/plain"})

				logger.info("Cleaning up {} files".format(len(filenames)))

				# Get current .py and .mpy files
				flash_files = [f for f in os.listdir() if f.endswith(".py") or f.endswith(".mpy")]

				# Delete any .py files only if .mpy is also present
				removed = []
				for f in filenames:
					py_name = f.split(".")[0] + ".py"
					mpy_name = f.split(".")[0] + ".mpy"
					if mpy_name in flash_files and py_name in flash_files:
						try:
							os.remove(py_name)
							removed.append(py_name)
							logger.info("cleanup: Removed file {}".format(py_name))
						except Exception as e:
							logger.error("cleanup: Failed to remove {}: {}".format(py_name, e))

				if removed:
					return microdot.Response("Removed {} .py files: {}".format(len(removed), ", ".join(removed)), 
							 status_code=200, headers={"Content-Type": "text/plain"})
				else:
					return microdot.Response("No .py files to remove", 
							 status_code=200, headers={"Content-Type": "text/plain"})

			except Exception as e:
				logger.error("Cleanup failed: {}".format(e))
				return microdot.Response("<h3>error during file cleanup: {}: {}</h3>".format(f, e), 
							 status_code=500, headers={"Content-Type": "text/html"} )

		@self.route("/remove/<filename>")
		async def remove_file(request, filename):
			if not self._require_auth(request):
				return microdot.Response.redirect("/")

			try:
				safe_name = self._sanitize_filename(filename)
			except Exception as e:
				return microdot.Response("Invalid filename", status_code=400)

			try:
				os.remove(safe_name)
				logger.info("Removed: {}".format(safe_name))
				return microdot.Response("Removed: {}".format(safe_name), headers={"Content-Type": "text/plain"})
			except OSError:
				logger.error("Error removing: {}".format(safe_name))
				return microdot.Response("Error removing: {}".format(safe_name), headers={"Content-Type": "text/plain"})

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
			logger.info("SHA256({}) = {}".format(safe_name, hexval))

			# Plain text output
			return microdot.Response(hexval, headers={"Content-Type": "text/plain"})

		# Add memory error handling? for tail_console: Exception: memory allocation failed, allocating 131072 bytes
		# air-s3 was getting this error and not doing a tail_console at the time?
		
		@self.route('/tail_console')
		@with_sse
		async def tail_console(request, sse):
			
			if not self._require_auth(request):
				return microdot.Response('Unauthorized', status_code=401)

			error_count = 0
			client_connected = True
			logger.debug(f"tail_console opened: request: {request}, sse: {sse}")
			
			# send exceptions to the client
			for e in logger.exception_history:
				for each_line in e.split("\n"):
					await sse.send( each_line )
					await sse.send( "" )

			while client_connected:
				try:
					async for log_level, line in logger.console_history:
						if len(line) > 500:
							line  = f"({len(line)}) !> {line[0:80]} <!"
						await sse.send( line.strip() )
						await sse.send( "" )

				except asyncio.CancelledError:
					logger.error(f"tail_console: asyncio.CancelledError for sse: {sse}")
					client_connected = False

				except Exception as e:
					exception_buffer = StringIO()
					sys.print_exception(e, exception_buffer)
					logger._exception(exception_buffer.getvalue(), func_name='tail_console', count=error_count)
					error_count += 1
					
		@self.route('/cmd/<cmd>')
		async def cmd(request, cmd):
			# if not self._require_auth(request):
			# 	return microdot.Response('Unauthorized', status_code=401)

			try:
				return microdot.Response(str( eval(cmd) ), headers={"Content-Type": "text/plain"})
			except Exception as e:
				return microdot.Response(str(e), headers={"Content-Type": "text/plain"})


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
