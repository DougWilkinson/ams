# randerr.py
# generate random exceptions

from versions import versions
versions[__name__] = 1
# 1: initial version

import asyncio
from logger import info, error
from system import exception_handler, start
from random import randrange

# list of real exceptions to generate based on number
random_exceptions = {
	0: "IndexError",
	1: "RandomError",
	2: "ValueError",
	3: "UnknownError",
	4: "RuntimeError"
}

@exception_handler
async def randerr():
	info("randerr: running")
	await asyncio.sleep(5)
	while True:
		s = randrange(1, 45)
		info(f"randerr: sleeping {s} seconds")
		await asyncio.sleep(s)

		info("randerr: generating random exception")
		raise Exception(random_exceptions[randrange(0, len(random_exceptions))])

start(randerr)