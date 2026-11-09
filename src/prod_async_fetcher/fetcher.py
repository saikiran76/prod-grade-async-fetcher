from prod_async_fetcher.config import Config
import httpx

class Fetcher:
    def __init__(self, config: Config):
        self.config = config
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout = self.config.timeout_secs,
            headers = {
                "User-agent": self.config.user_agent
            }
        )

        
        return self
    
    async def __aexit__(self):
        await self.client.aclose()
        self.client = None

    async def fetch_response(self, url: str) -> httpx.Response:
        return await self.client.get(url)

