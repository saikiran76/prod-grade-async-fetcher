import urllib.robotparser as rpt
from urllib.parse import urlsplit
import httpx
from prod_async_fetcher.config import Config

from dataclasses import dataclass

@dataclass(frozen = True, slots = True)
class RobotsRule:
    path: str
    allowed: bool
class RobotChecker:
    def __init__(self, client, config):
        self.cfg = config
        self.client = client
        self.robots_cache: RobotsRule = {}
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

    def transform_rules(self, rules: list) -> list[RobotsRule]:
        transformed_rules: list[RobotsRule] = []
        for rule in (rules):
            colon_idx = rule.find(':')
            if colon_idx != -1:
                # transformed_rules.append({
                #     'path': rule[colon_idx+2:]
                # })
                path = rule[colon_idx+1:].strip()
                if not path:
                    continue
                if rule[: colon_idx].strip().lower() == 'allow':
                    # transformed_rules.append({
                    #     'path': rule[colon_idx+2:],
                    #     'allowed': True
                    # })
                    transformed_rules.append(
                        RobotsRule(
                            path=path,
                            allowed=True
                        )
                    )
                elif rule[: colon_idx].strip().lower() == 'disallow':
                    # transformed_rules.append({
                    #     'path': rule[colon_idx+2:],
                    #     'allowed': False
                    # })
                    transformed_rules.append(
                        RobotsRule(
                            path=path,
                            allowed=False
                        )
                    )
        return transformed_rules

    async def extract_rules(self, url:str):
        robots_url = self.point_to_root(url)
        res = await self.client.get(robots_url)

        if res.text:
            rules = res.text.strip()
            lines = rules.split('\n')

            trans_rules = self.transform_rules(lines)

            return trans_rules
        
        return []
    
    async def is_allowed(self, url:str) -> bool:
        # extract path
        path = urlsplit(url).path

        if path:
            rules = await self.extract_rules(url)
            paths = [rule.path for rule in rules if rule.allowed]
            print('[debug] allowed paths: ', paths)
            if path in paths:
                return True
            else:
                return False
        
        raise('path extraction failed for the given URL')

    
    
                



    async def fetch_parse(self, url:str):
        # self.rp.read(f'{self.point_to_root(self.url)}robots.txt')
        org = self.derive_origin(url)
        # if not self.robots_cache or (rp.mtime == 0):
        if org in self.robots_cache:
            return self.robots_cache[org]

        robots_url = self.point_to_root(url)
        res = await self.client.get(robots_url)
        rp = rpt.RobotFileParser()

        rp.set_url(robots_url)
        print("[debug] the rules: ", res.text.splitlines())
        rp.parse(res.text.splitlines())
        rp.modified()
        print("[debug] Default user agents:", rp.default_entry.useragents)

        print('[debug] checking some props:',[(rule.path, rule.allowance, len(rule.path)) for rule in rp.default_entry.rulelines])

        print('[debug] checking permissions: ', rp.can_fetch(self.cfg.user_agent, "https://example.com/private/"))
        print('[debug] checking permissions for /private/public: ', rp.can_fetch(self.cfg.user_agent, "https://example.com/private/public"))
        self.robots_cache[org] = rp

        print('[debug] checking the parsed entries: ', f'{rp.entries}\n')
        print('[debug] the default entry: ', f'{rp.default_entry}')

            
        return rp
    
    ## checking permissions
    # async def check(self, url:str) -> bool:
    #     ## our crawler is allowed to access that URL? check the permission
    #     cache = self.robots_cache
    #     if cache:
    #         org = self.derive_origin(url)
    #         parser = cache[org]
    #         return parser.can_fetch(self.cfg.user_agent, url)
    #     else:
    #         rp = await self.fetch_parse(url)
    #         return parser.can_fetch(self.cfg.user_agent, url)

    async def check(self, url: str) -> bool:
        parser = await self.fetch_parse(url)
        return parser.can_fetch(self.cfg.user_agent, url)

        # rp = self.fetch_parse(url)
        # return rp.can_fetch(self.cfg.user_agent, f'{self.derive_origin(url)}')


    


