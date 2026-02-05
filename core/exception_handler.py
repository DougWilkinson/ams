from sys import print_exception
from io import StringIO
import asyncio
exception_buffer = StringIO()


def wraps(wrapped, assigned=('__module__', '__name__', '__doc__')):
	def wrapper(f):
		for attr in assigned:
			try:
				setattr(f, attr, getattr(wrapped, attr))
			except AttributeError:
				pass
		return f
	return wrapper

from localtime import offset_time

class ExceptionDetail:
	def __init__(self, function_name, exception):
		self.function_name = function_name
		self.exception = exception
		self.timestamp = offset_time()

	@property
	def name(self):
		return self.function_name
	
	@property
	def timestamp(self):
		return self.timestamp
	
	@property
	def exception(self):
		return self.exception
	
exceptions = {"total": 0}

def exception_handler(func):
	@wraps(func)
	async def wrapped(*args, **kwargs):
		while True:
			print("starting: ", func.__name__)
			try:
				await func( *args, **kwargs )
			except KeyboardInterrupt:
				break
			except Exception as e:
				exception_buffer = StringIO()
				print_exception(e, exception_buffer)
				print("Error during: ", func.__name__)
				print(exception_buffer.getvalue())
	return wrapped

@exception_handler
async def bad_coro():
	i = 0
	print("starting bad_coro")
	while True:
		print("processing .. ", i)
		i += 1
		await asyncio.sleep(1)
		if i % 10 == 0:
			raise Exception("bad function error")

async def main():
	await asyncio.sleep(100)

