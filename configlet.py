# configlet.py

from versions import versions
versions[__name__] = 1

from appserver import app, Response
import asyncio

from settings import config, info, error, debug, start, masked_values
# from microdot import Microdot, Response
# import network
import re  # MicroPython regex
import time

# config_server_captive.py
import json
# import socket
# import os

# Helpers
def percent_decode(s):
    """Simple percent-decode and '+'->space for application/x-www-form-urlencoded values."""
    # replace + with space
    s = s.replace('+', ' ')
    # decode %xx
    i = 0
    out = []
    while i < len(s):
        ch = s[i]
        if ch == '%' and i + 2 < len(s):
            try:
                hexval = int(s[i+1:i+3], 16)
                out.append(chr(hexval))
                i += 3
                continue
            except:
                # fallthrough if malformed
                out.append('%')
        else:
            out.append(ch)
        i += 1
    return ''.join(out)

def html_escape(s):
    if s is None:
        return ""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;"))


template_html = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta charset="utf-8">
  <title>ESP32 Configuration</title>
  <style>
    body {{ font-family: Arial,Helvetica,sans-serif; margin: 0; padding: 20px; background: #f7f7f7; }}
    .card {{ max-width: 480px; margin: auto; background: white; padding: 16px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.12); }}
    h2 {{ text-align:center; margin: 0 0 12px 0; }}
    label {{ display:block; font-weight:600; margin-top: 10px; }}
    input[type=text] {{ width:100%; padding:10px; margin-top:6px; box-sizing:border-box; font-size:16px; border:1px solid #ccc; border-radius:4px; }}
    .submit {{ width:100%; margin-top:14px; padding:12px; font-size:16px; background:#007bff; color:#fff; border:none; border-radius:6px; }}
    .notice {{ margin-top:10px; color: #006400; font-weight:600; }}
    .small {{ font-size:12px; color:#666; margin-top:8px; text-align:center; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Device Configuration</h2>
    <form method="POST" id="cfgform">
      {fields}
      <input class="submit" type="submit" value="Update">
    </form>
    {notice_block}
    <p class="small">Connect to Wi-Fi: <strong>{ssid}</strong></p>
  </div>

  <script>
  (function(){{
    // after successful POST the server returns this same page; optionally try to close
    var f = document.getElementById('cfgform');
    f.addEventListener('submit', function(){{
      // show saving message quickly (submit will navigate)
      // captive portals might not allow scripts to close window reliably
      setTimeout(function(){{ try{{ window.close(); }}catch(e){{}} }}, 1000);
    }});
  }})();
  </script>
</body>
</html>
"""

Response.default_content_type = "text/html"

# --- Mobile-friendly HTML form ---
def html_form():
	# simple JS to attempt to close captive portal after successful submit
	# (many captive assistants ignore window.close(), but it's harmless)
	fields_html = ""
	for k, v in config.persistent.items():
		if type(v) != str:
			continue
		
		fields_html += "<label>{k}:</label><input type='{input_type}' autocapitalize='none' name='{k}' value='{val}'>\n".format(
			k=html_escape(k), val=html_escape(v), input_type="password" if k in masked_values else "text")

	return template_html.format(fields=fields_html, notice_block=("<div class='notice'>{}</div>".format(html_escape(""))),
                 ssid=html_escape(config.wifi_ssid))

# --- Request body parsing for form data ---
def parse_form(body):
	params = {}
	if not body:
		return params
	if isinstance(body, bytes):
		try:
			body = body.decode()
		except:
			body = str(body)
	for pair in body.split("&"):
		if "=" in pair:
			k, v = pair.split("=", 1)
			k = percent_decode(k)
			v = percent_decode(v)
			params[k] = v
	return params

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
async def index(request):
	if request.method == "POST":
		body = request.body or ""
		params = parse_form(body)
		# update only known keys
		for k,v in config.persistent.items():
			if k in params and params[k] != v:
				config.set_value(k, params[k])
	return html_form()

# Android captive portal check
@app.route("/generate_204")
async def android_cna(request):
	# Android expects a 204 for no captive portal. Return redirect to show portal.
	# Some Android versions accept 302; return 302 to root.
	return "", 302, {"Location": "/"}

# iOS/macOS captive portal detection
@app.route("/hotspot-detect.html")
async def apple_cna(request):
	# Return a small HTML with meta-refresh to root; this triggers the captive portal.
	html = ("<html><head>"
			"<meta http-equiv='refresh' content='0; url=/' />"
			"<title>Redirecting...</title></head>"
			"<body>Redirecting to configuration page...</body></html>")
	return html

# Common Windows checks
@app.route("/connecttest.txt")
@app.route("/ncsi.txt")
async def windows_cna(request):
	# Windows expects specific content; redirect to portal instead
	return "", 302, {"Location": "/"}

# Apple's other success URL some devices hit
@app.route("/library/test/success.html")
@app.route("/www.apple.com/library/test/success.html")
async def apple_success_like(request):
	# Respond with a redirect / portal page — any response other than Apple's "Success" text triggers captive portal
	html = ("<html><head><meta http-equiv='refresh' content='0; url=/' /><title>Login</title></head>"
			"<body>Redirecting to configuration page...</body></html>")
	return html

# Catch-all: serve portal HTML directly for any other path - important for captive assistants
@app.route("/<path:path>")
async def catch_all(request, path):
	return html_form()


