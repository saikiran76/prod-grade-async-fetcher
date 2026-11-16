import httpx
import asyncio
from prod_async_fetcher.robots import RobotChecker
from prod_async_fetcher.config import Config

from textwrap import dedent 

async def test():
    robots_content =robots_content = """
    User-agent: *
    Disallow: /private/
    Allow: /private/public/
    Disallow: /admin/
    Allow: /articles/
    Disallow: /*.pdf$
    Allow: /public/*
    Disallow: /admin/$
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
        url0 = "https://example.com/private/"
        url2 = "https://example.com/private/public/"
        url3 = "https://example.com/private/secrets/"
        url4 = "https://example.com/private/public/secrets"
        url5 = "https://example.com/document.pdf"
        url6 = "https://example.com/document.pdf/archive"
        url7 = "https://example.com/admin/dashboard/"

        # print(await checker.check(url1))
        # print(await checker.extract_rules(url2))
        print("url - /private/public:", await checker.is_allowed(url2))
        print("url- /private/secrets/: ", await checker.is_allowed(url3))# print(await checker.check(url2))
        print("url: /private/public/secrets: ", await checker.is_allowed(url4))# print(await checker.check(url3))
        print("url: /document.pdf: " , await checker.is_allowed(url5))
        print("url: /document.pdf/archive: ", await checker.is_allowed(url6))
        print("url: /admin/dashboard/: ", await checker.is_allowed(url7))
                # print("Cache:", checker.robots_cache.keys())

    finally:
        await client.aclose()

asyncio.run(test())