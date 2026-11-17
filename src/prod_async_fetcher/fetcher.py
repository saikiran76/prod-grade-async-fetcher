from prod_async_fetcher.config import Config
from prod_async_fetcher.models import Page, Status
import httpx
import asyncio
from urllib.parse import urlsplit
# from contextlib import asynccontextmanager
import random
from datetime import datetime, timezone
# from dataclasses import dataclass

from prod_async_fetcher.robots import RobotChecker
from prod_async_fetcher.rate_limiter import RateLimiter


class Fetcher:
    def __init__(self, config: Config):
        self.config = config
        self.client: httpx.AsyncClient | None = None
        self.semaphore = asyncio.Semaphore( ## sharable semaphore
            self.config.concurrency
        )
        # self.robot_checker = RobotChecker(self.client, config)
        self.rate_limiter = RateLimiter(config.requests_per_sec_per_host)

        ## temporary attrs for testing
        self.active_reqs = 0
        self.max_active_reqs = 0

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout = self.config.timeout_secs,
            headers = {
                "User-agent": self.config.user_agent
            },
            follow_redirects=True # reason?
        )

        # initialising robot checker here
        self.robot_checker = RobotChecker(self.client, self.config) #what
        
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.client is not None: ## None is already falsy - bug fix
            await self.client.aclose()
            self.client = None

    async def fetch_response(self, url: str) -> Page:
        ## only fetching when client is available
        if self.client is None: ## protecting the HTTP request with the semaphore
            raise RuntimeError("No active client!")
        
        allowed = await self.robot_checker.is_allowed(url)
        
        if not allowed:
            return Page(
                url = url,
                attempts = 0,
                fetched_at=datetime.now(
                    timezone.utc
                ),
                status = Status.BLOCKED_BY_ROBOTS
            )
            
            # Had to remove the following try/catch as excpetions might contain invaluable info and we aren't catching them exactly
            # try:
            #     return await self.client.get(url)
            # except:
            #     raise Exception("There is a runtime error!")
            # else: -- this is unreachable btw as we are returning in try block
            #     print("fetch success!")

        host = urlsplit(url).netloc ## host 

        res, attempts = await self.fetch_response_retry(url)

        if res is None:
            return Page(
                url=url,
                attempts=attempts,
                fetched_at=datetime.now(timezone.utc),
                status=Status.NETWORK_ERROR
            )
        
        if not 200 <= res.status_code <300:
            status = Status.HTTP_ERROR
        elif "text/html" not in res.headers.get(
            "content-type", ""
        ).lower():
            status = Status.NOT_HTML
        else:
            status = Status.OK
        # await self.rate_limiter.acquire(host) # removed redundant rate-limiting call here

        return Page(
            url=str(res.url),
            attempts=attempts,
            fetched_at = datetime.now(timezone.utc),
            status=status
        )
    
        # async with self.semaphore:
        #     self.active_reqs += 1
        #     try:
        #         self.max_active_reqs = max(self.active_reqs, self.max_active_reqs)
        #         return await self.client.get(url)
        #     finally:
        #         self.active_reqs-=1
        #         print("maximum reqs at this point: ", self.max_active_reqs)
    




    # @asynccontextmanager
    # async def early_release_semaphore(self, sem: asyncio.Semaphore):
    # released = False
    # await sem.acquire()

    # def release():
    #     nonlocal released
    #     if not released:
    #         sem.release()
    #         released = True

    # try:
    #     yield release
    # finally:
    #     release()    

    async def fetch_response_retry(self, url: str) -> tuple[httpx.Response | None, int]:
        if self.client is None:
            raise RuntimeError("No active client though!")
        
        retry_status = {429, 500, 502, 503, 504}
        last_res = None

        host = urlsplit(url).netloc # for rate-limiting


        for attempt in range(1, self.config.max_attempts+1):
            try:
                should_retry = False
                # As every retry is a new HTTP request, it must also respect host rate-limit
                await self.rate_limiter.acquire(host)

                async with self.semaphore:
                    res = await self.client.get(url)
                last_res = res

                if res.status_code not in retry_status:
                    return res, attempt
                else:
                    should_retry = True
            
            except httpx.TransportError:
                should_retry = True
                if attempt == self.config.max_attempts:
                    return None, attempt
                
                if should_retry and attempt < self.config.max_attempts:
                    base_delay = min(0.5*(2**(attempt-1)), 8.0)
                    delay = random.uniform(0, base_delay)
                    await asyncio.sleep(delay)
        return last_res, self.config.max_attempts
                

        # while attempt < self.config.max_attempts:
        #     attempt += 1
        #     try:
        #         async with self.semaphore:
        #             res = await self.client.get(url)
                
        #         # early releasing (already the semaphore is released at this point)
        #         ## We are writing the delays and creating a sleep coroutine before deciding to retry, this should be fixed!
        #         status_codes = [429, 500, 502, 503, 504]
                
        #         if res.status_code in status_codes:
        #             '''
        #             only when the response code matches, calculate the delays 
        #             '''
        #             base_delay = 0.5*(2**(attempt -1))
        #             delay = random.uniform(0, base_delay)
        #             await asyncio.sleep(3)
        #             continue
                    
        #         # match res.status_code:
        #         #     case 429:
        #         #         if attempt < self.config.max_attempts:
        #         #             await sleep
        #         #             ## initiaiting another request here
        #         #             continue
        #         #     case 500:
        #         #         if attempt < self.config.max_attempts:
        #         #             await sleep
        #         #             continue
        #         #     case 502:
        #         #         if attempt < self.config.max_attempts:
        #         #             await sleep
        #         #             continue
        #         #     case 503:
        #         #         if attempt < self.config.max_attempts:
        #         #             await sleep
        #         #             continue
        #         #     case 504:
        #         #         if attempt < self.config.max_attempts:
        #         #             await sleep
        #         #             continue
        #         print("request fulfilled with status code: ", res.status_code)
        #         return res  

        #     except httpx.TransportError:
        #         raise
        #     ## transport errored requests can also be retried! can do this later.


                
                

