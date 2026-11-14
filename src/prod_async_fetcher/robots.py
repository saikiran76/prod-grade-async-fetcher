import urllib.robotparser as rpt
from urllib.parse import urlsplit
import httpx
from prod_async_fetcher.config import Config

class RobotChecker:
    def __init__(self, client, config):
        self.cfg = config
        self.client = client
        self.robots_cache = {}
        # self.url = url
        # self.rp = rpt.RobotFileParser()
    
    def derive_origin(self, url:str) -> str:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        return origin

    
    def point_to_root(self, url:str) -> str:
        # self.rp = rpt.RobotFileParser()
        return f'{self.derive_origin(url)}/robots.txt'

    '''
    downloads the text, and parses all the Allow, Disallow, and Crawl-delay rules into memory.

    Expected return value from the server:
    User-agent: *
    Disallow: /private/
    Allow: /private/public/
    Crawl-delay: 2

    parser converts these textual directives into rules it can evaluate.
    '''

    async def fetch_parse(self, url:str):
        # self.rp.read(f'{self.point_to_root(self.url)}robots.txt')
        org = self.derive_origin(url)

        robots_url = self.point_to_root(url)
        res = await self.client.get(robots_url)
        rp = rpt.RobotFileParser()

        # if not self.robots_cache or (rp.mtime == 0):
        if org not in self.robots_cache:
            rp.set_url(robots_url)
            rp.parse(res.text.splitlines())
            self.robots_cache[org] = rp
        else:
            return self.robots_cache ## return the rp early if already cached
        return rp
    
    ## checking permissions
    async def check(self, url:str) -> bool:
        ## our crawler is allowed to access that URL? check the permission
        cache = self.robots_cache
        if cache:
            org = self.derive_origin(url)
            parser = cache[org]
            return parser.can_fetch(self.cfg.user_agent, url)
        else:
            rp = await self.fetch_parse(url)
            return parser.can_fetch(self.cfg.user_agent, url)

        # rp = self.fetch_parse(url)
        # return rp.can_fetch(self.cfg.user_agent, f'{self.derive_origin(url)}')


    


