import httpx
import asyncio
from prod_async_fetcher.robots import RobotChecker
from prod_async_fetcher.config import Config

from textwrap import dedent 

async def test():
    robots_content = """
        User-agent: *
        Disallow: /private/
        Allow: /private/public/
    """

    async def handler(request):
        print("Fetching:", request.url)
        return httpx.Response(
            200,
            text=dedent(robots_content).strip(),
            request=request
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    checker = RobotChecker(client, Config())

    try:
        url1 = "https://example.com/private/"
        url2 = "https://example.com/private/public/"
        url3 = "https://example.com/articles/"

        print(await checker.check(url1))
        print(await checker.check(url2))
        print(await checker.check(url3))

        print("Cache:", checker.robots_cache.keys())

    finally:
        await client.aclose()

asyncio.run(test())