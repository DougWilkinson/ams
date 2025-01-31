#webcam.py

from versions import versions
versions[__name__] = 1

from core import info, latch
from ov2640 import OV2640,OV2640_1600x1200_JPEG, OV2640_1024x768_JPEG, OV2640_1280x1024_JPEG
from microdot import Microdot
from singlequeue import SingleQueue
import asyncio

cam = OV2640(resolution=OV2640_1280x1024_JPEG)
app = Microdot()

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
        </div>
    </body>
</html>
'''

images = SingleQueue(5)

async def queue_image(cam):
	while True:
		images.put(cam.get_image())
		info("wi: {} ri: {} discards: {}".format(images._wi, images._ri, images.discards) )
		await asyncio.sleep(.05)

asyncio.create_task(queue_image(cam)
					)
@app.route('/stream')
async def stream(request):
	info('grabbing snapshot')
	return images, {'Content-Type': 'multipart/x-mixed-replace; boundary=frame'} 

@app.route('/')
async def hello(request):
    return html, 200, {'Content-Type': 'text/html'}


@app.route('/shutdown')
async def shutdown(request):
    request.app.shutdown()
    return 'The server is shutting down...'


app.run(debug=True)

