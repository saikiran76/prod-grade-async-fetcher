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
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.client is not None: ## None is already falsy - bug fix
            await self.client.aclose()
            self.client = None

    async def fetch_response(self, url: str) -> httpx.Response:
        ## only fetching when client is available
        if self.client:
            return await self.client.get(url)
            # Had to remove the following try/catch as excpetions might contain invaluable info and we aren't catching them exactly
            # try:
            #     return await self.client.get(url)
            # except:
            #     raise Exception("There is a runtime error!")
            # else: -- this is unreachable btw as we are returning in try block
            #     print("fetch success!")
        else:
            raise RuntimeError("No active client!")

