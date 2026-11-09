import asyncio

from prod_async_fetcher.config import Config
from prod_async_fetcher.fetcher import Fetcher

async def main():
    async with Fetcher(Config()) as fetcher:
        res = await fetcher.fetch_response("https://example.com")
        print(res.status_code)
        print(res.headers.get('content-type'))
        print(res.text[:200])

asyncio.run(main())