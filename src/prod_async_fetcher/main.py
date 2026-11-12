import asyncio
import httpx

from prod_async_fetcher.config import Config
from prod_async_fetcher.fetcher import Fetcher




async def main():
    statuses = iter([503, 503, 200])
    async def handler(req):
        status = next(statuses)
        print(f'running the simulated server: {status}')
        return httpx.Response(status, request=req)
    
    transport = httpx.MockTransport(handler)

    fetcher = Fetcher(Config())
    client = httpx.AsyncClient(transport=transport)
    fetcher.client = client

    try:
        # async with fetcher:
        res = await fetcher.fetch_response_retry(url="https://example.com")
        print("Final response:", res.status_code)
    finally:
        await client.aclose()
    # async with Fetcher(Config()) as fetcher:
    #     client = fetcher.client
    #     # res = await fetcher.fetch_response("https://example.com")
    #     urls = [
    #         "https://example.com",
    #         "https://httpbin.org/get",
    #         "https://www.python.org",
    #         "https://www.wikipedia.org",
    #         "https://www.github.com",
    #     ]
    #     cs = [fetcher.fetch_response(url) for url in urls]
 
    #     res = await asyncio.gather(
    #         *cs
    #     )
            
    #     # print("Status: ", res.status_code)
    #     print("responses: ", res)
    #     # print(res.headers.get('content-type'))
    #     # print(res.text[:200])
    #     print("Close inside context: ", client.is_closed)
    # print("closed after context: ", client.is_closed)
    # print("fetcher client after context: ", fetcher.client)



asyncio.run(main())