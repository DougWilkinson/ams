#espcam.py

from versions import versions
versions[__name__] = 1

from core import info, latch, load_config
from ov2640 import OV2640, resolutions
from microdot import Microdot
#from singlequeue import SingleQueue
from msgqueue import MsgQueue
import asyncio
import json

settings = load_config(name="camera", key="settings")
if not settings:
	settings = { "resolution": "OV2640_640x480_JPEG", "fps": "2" }

cam = OV2640(resolution=settings["resolution"])
app = Microdot()

settings_page = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Camera Settings</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 50px;
    }}
    .button {{
      background-color: #007bff;
      color: white;
      padding: 10px 20px;
      margin: 10px;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-size: 16px;
    }}
    .button:hover {{
      background-color: #0056b3;
    }}
	#image-frame {{
      margin-top: 30px;
      width: 80%;
      max-width: 600px;
      height: 400px;
      border: 2px solid #ccc;
    }}
    iframe {{
      width: 100%;
      height: 100%;
      border: none;
    }}

  </style>
</head>
<body>
  <h1>Resolution: {}</h1>
  <h1>frames/sec: {}</h1>
  <p><a href="/stream">Stream</a></p>
  {}
  <div id="image-frame">
    <iframe id="display-frame" src="/stream" title="Image Frame"></iframe>
  </div>

  <script>
    function changeResolution(url) {{
      window.location.href = url;
    }}
  </script>
</body>
</html>
'''

html = '''<!DOCTYPE html>
<html>
    <head>
        <title>Microdot Example Page</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <div>
            <h1>Microdot Example Page</h1>
            <p>Hello from Microdot!</p>
            <p><a href="/shutdown">Click to shutdown the server</a></p>
            {}
        </div>
    </body>
</html>
'''

streaming = asyncio.Event()
last_image = [0, 0]
fps=2

def build_menu():
	options = ""
	for res in resolutions:
		button_def = '    <button class="button" onclick="changeResolution(\'/res/{}\')">{}</button>'.format(res, res)
		#button_def = "            <p><a href='/res/{}'>{}</a>".format(res, res)
		options += button_def

	return settings_page.format(cam.resolution, fps, options)

async def stage_image():
	global streaming
	seq = 0
	sleep_fps = 1/fps
	while True:
		if streaming.is_set():
			last_image[0] = seq
			seq += 1
			last_image[1] = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + cam.get_image() 
		await asyncio.sleep(sleep_fps)

asyncio.create_task(stage_image() )

async def stream_image(socket, image_queue):
	global streaming
	last_seq = 0
	sleep_fps = 1/(fps+1)
	info("streaming started: socket_fileno: {}".format(socket.fileno() ) )
	while socket.fileno() > 0:
		streaming.set()
		# b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
		#image_queue.put(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + cam.get_image())
		if last_image[0] > last_seq:
			last_seq = last_image[0] 
			image_queue.put(last_image[1])
			info("discards: {}".format(image_queue.discards) )
		await asyncio.sleep(sleep_fps)
	streaming.clear()
# asyncio.create_task(queue_image(cam) )
		
@app.route('/stream')
async def stream(request):
	#active_reqs.insert(0, request.sock[0])
	info('Starting stream task')
	image_queue = MsgQueue(1)
	asyncio.create_task(stream_image(request.sock[0].s, image_queue) )
	return image_queue, {'Content-Type': 'multipart/x-mixed-replace; boundary=frame'} 

# @app.after_request
# async def end_stream(request, response):
# 	info("{} {} {} {} {} {} {} {} {} {}".format(
# 		request.url, request.app, request.client_addr, 
# 		request.method, request.url, request.headers, 
# 		request.content_length, request.content_type, 
# 		request.http_version,
#         request.sock) )

@app.route('/frame')
async def stream(request):
	global streaming
	info("streaming: {}".format(streaming.is_set() ) )
	# take the last image from queue (newest)
	return cam.get_image(), {'Content-Type': 'image/jpeg'} 

@app.route('/')
async def hello(request):
    return build_menu(), 200, {'Content-Type': 'text/html'}


@app.route('/shutdown')
async def shutdown(request):
    request.app.shutdown()
    return 'The server is shutting down...'

@app.route('/res/<resolution>')
async def set_res(request, resolution):
	cam.resolution = resolution
	cam.setresolution()
	await asyncio.sleep(2)
	settings['resolution'] = resolution
	with open('camera', 'w') as f:
		f.write(json.dumps(settings) )
	return build_menu(), 200, {'Content-Type': 'text/html'}

#app.run(debug=True)
asyncio.create_task(app.start_server(host='0.0.0.0', port=5000, debug=False))

async def start(hostname):
		await latch.wait()

