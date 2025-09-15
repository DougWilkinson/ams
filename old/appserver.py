# appserver.py

from versions import versions
versions[__name__] = 1

# main authentication page
# home page with stats/overview
# profile select/edit/delete/add
# 
from microdot import Microdot, Response

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

# used to render config pages
config_template = """
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



authentication_template = """
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
      <label for="username">Username:</label>
      <input type="text" id="username" name="username" required>
      <label for="password">Password:</label>
      <input type="password" id="password" name="password" required>
      <input class="submit" type="submit" value="Login">
    </form>
    {notice_block}
    <p class="small">Connect to Wi-Fi: <strong>{ssid}</strong></p>
  </div>
</body>
</html>
"""

status_template = """
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
    .notice {{ margin-top:10px; color: #006400; font-weight:600; }}
    .small {{ font-size:12px; color:#666; margin-top:8px; text-align:center; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Device Configuration</h2>
    {notice_block}
    <p class="small">Connect to Wi-Fi: <strong>{ssid}</strong></p>
  </div>
</body>
</html>
"""


app = Microdot()
