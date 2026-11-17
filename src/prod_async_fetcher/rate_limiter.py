import asyncio


class RateLimiter:
    def __init__(self, requests_per_sec:float):
        # positive requests per sec value, ex: rqs = 10
        if requests_per_sec <= 0:
            raise ValueError("Requests per sec must be positive!")
        
        '''
        1 sec - n reqs (say 10 reqs), then interval = 1/rqs
        Ex: rqs = 10, then interval = 1/10
        '''
        self.interval = 1.0/requests_per_sec
        self.next_req: dict[str, float] = {}
        self.locks: dict[str, asyncio.Lock] = {}
    
    async def acquire(self, host: str) -> None:
        lock = self.locks.setdefault(
            host, 
            asyncio.Lock()
        )

        async with lock:
            loop = asyncio.get_running_loop()
            now = loop.time()

            next_time = self.next_req.get(host, now)

            wait = max(0.0, next_time-now)

            if wait:
                await asyncio.sleep(wait)
            
            self.next_req[host] = (
                max(now, next_time) + self.interval
            )
