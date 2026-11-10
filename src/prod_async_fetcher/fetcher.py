from prod_async_fetcher.config import Config
import httpx
import asyncio

class Fetcher:
    def __init__(self, config: Config):
        self.config = config
        self.client: httpx.AsyncClient | None = None
        self.semaphore = asyncio.Semaphore( ## sharable semaphore
            self.config.concurrency
        )
        ## temporary attrs for testing
        self.active_reqs = 0
        self.max_active_reqs = 0

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
        if self.client is None: ## protecting the HTTP request with the semaphore
            raise RuntimeError("No active client!")
            
            # Had to remove the following try/catch as excpetions might contain invaluable info and we aren't catching them exactly
            # try:
            #     return await self.client.get(url)
            # except:
            #     raise Exception("There is a runtime error!")
            # else: -- this is unreachable btw as we are returning in try block
            #     print("fetch success!")
        else:
            async with self.semaphore:
                self.active_reqs += 1
                try:
                    self.max_active_reqs = max(self.active_reqs, self.max_active_reqs)
                    return await self.client.get(url)
                finally:
                    self.active_reqs-=1
                    print("maximum reqs at this point: ", self.max_active_reqs)

                
                

