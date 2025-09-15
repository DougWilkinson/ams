#zerocam.py

import cv2
from microdot import Microdot
#from zeroqueue import SingleQueue
import asyncio
from time import localtime
cam = cv2.VideoCapture(0)
app = Microdot()

def error(msg):
	info(msg, lev=0, color='\u001b[31m', end="\n")

def info(msg, lev=2, color='\u001b[0m', end="\n"):
	if True:
		# get time with offset
		dt = localtime()
		print("{}{:02d}:{:02d}:{:02d}: {}{}".format( color,
			dt[3], dt[4], dt[5], 
			msg, "\u001b[0m" ), end=end )

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

options = '<p><a href="/stream">Click to stream video</a></p>'
# for res in resolutions:
#     button_def = "            <p><a href='/res/{}'>{}</a>".format(res, res)
#     options += button_def

menu = html.format(options)

main_loop = asyncio.new_event_loop()
queue_event = asyncio.Event()
class SingleQueue:
	def __init__(self, size):
		self._q = [0 for _ in range(max(size, 4))]
		self._size = size
		self._wi = 0
		self._ri = 0
		self._evt = asyncio.Event()
		self.discards = 0

	def put(self, v):
		self._q[self._wi] = v
		self._evt.set()
		self._wi = (self._wi + 1) % self._size
		if self._wi == self._ri:  # Would indicate empty
			self._ri = (self._ri + 1) % self._size  # Discard a message
			self.discards += 1

	def __aiter__(self):
		return self

	async def __anext__(self):
		if self._ri == self._wi:  # Empty
			self._evt.clear()
			await self._evt.wait()
		r = self._q[self._ri]
		self._ri = (self._ri + 1) % self._size
		return r


async def queue_image(cam):
	global images
	images = SingleQueue(5)
	info("queue_image started")
	while True:
		r, image = cam.read()
		if r:
			r, jpg = cv2.imencode('.jpg', image)
			if r:
				images.put(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytes(jpg))
				#info("length= {}, discards: {}".format(len(jpg), images.discards) )
		await asyncio.sleep(.05)

main_loop.create_task(queue_image(cam))
# asyncio.create_task(queue_image(cam)

@app.route('/stream')
async def stream(request):
	info('grabbing snapshot')
	return images, {'Content-Type': 'multipart/x-mixed-replace; boundary=frame'} 

@app.route('/')
async def hello(request):
	return menu, 200, {'Content-Type': 'text/html'}


@app.route('/shutdown')
async def shutdown(request):
	request.app.shutdown()
	cam.release()
	return 'The server is shutting down...'

# @app.route('/res/<resolution>')
# async def set_res(request, resolution):
#     cam.setresolution(resolutions[resolution])
#     return "Resolution set to {}".format(resolution)

main_loop.create_task(app.start_server(host='0.0.0.0', port=5000, debug=True))
#app.run(debug=True)
main_loop.run_forever()

