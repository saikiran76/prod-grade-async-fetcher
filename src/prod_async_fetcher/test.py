import httpx
import asyncio
from prod_async_fetcher.robots import RobotChecker
from prod_async_fetcher.config import Config

from textwrap import dedent 

async def test():
    robots_content = """\
    User-agent: *
    Disallow: /private/
    Allow: /private/public/
    Disallow: /admin/
    Allow: /articles/
    Disallow:
    Invalid directive
    """

    async def handler(request):
        print("[debug] Fetching:", request.url)
        dedented_robots = dedent(robots_content).strip()
        print("[debug] dedented content: ", dedented_robots)
        print("[debug] checking the response: ", httpx.Response(
            200, text = dedented_robots, request=request
        ))
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

        # print(await checker.check(url1))
        print(await checker.extract_rules(url2))
        print(await checker.is_allowed(url2))
        # print(await checker.check(url2))
        # print(await checker.check(url3))

        # print("Cache:", checker.robots_cache.keys())

    finally:
        await client.aclose()

asyncio.run(test())