# import urllib.robotparser as rpt
from urllib.parse import urlsplit
import httpx
from prod_async_fetcher.config import Config
from dataclasses import dataclass, field
import re
import asyncio

@dataclass(frozen = True, slots = True)
class RobotsRule:
    path: str
    allowed: bool

@dataclass(slots=True)
class RobotsGroup:
    user_agents: list[str] = field(default_factory=list)
    rules: list[RobotsRule] = field(default_factory=list)

class RobotChecker:
    def __init__(self, client, config):
        self.cfg = config
        self.client = client
        self.robots_cache: dict[str, list[RobotsRule]] = {}
        self.locks: dict[str, asyncio.Lock] = {}
        # self.url = url
        # self.rp = rpt.RobotFileParser()
    
    def derive_origin(self, url:str) -> str:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        return origin
    
    def point_to_root(self, url:str) -> str:
        # self.rp = rpt.RobotFileParser()
        return f'{self.derive_origin(url)}/robots.txt'
    
    def parse_rules(self, text: str) -> list[RobotsGroup]:
        groups: list[RobotsGroup] = []
        agents: list[str] = []
        rules: list[RobotsRule] = []
        has_rules = False

        def finish_group():
            nonlocal agents, rules, has_rules
            if agents:
                groups.append(RobotsGroup(agents, rules))
            agents, rules, has_rules = [], [], False

        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue

            directive, value = line.split(":", 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == "user-agent":
                if has_rules:
                    finish_group()
                agents.append(value.lower())
            elif directive in {"allow", "disallow"} and agents:
                has_rules = True
                if value:
                    rules.append(
                        RobotsRule(
                            path=value,
                            allowed=(directive == "allow"),
                        )
                    )

        finish_group()
        return groups

    def select_rules(self, groups: list[RobotsGroup]) -> list[RobotsRule]:
        agent = self.cfg.user_agent.split("/", 1)[0].lower()

        specific: list[RobotsRule] = []
        wildcard: list[RobotsRule] = []

        for group in groups:
            if "*" in group.user_agents:
                wildcard.extend(group.rules)
            elif any(token and token in agent for token in group.user_agents):
                specific.extend(group.rules)

        return specific if specific else wildcard
    
    def rule_matches(self, rule_path: str, url_path: str) -> bool:
        # wildcard helper
        anchored = rule_path.endswith("$")

        if anchored:
            rule_path = rule_path[:-1]

        pattern = re.escape(rule_path)
        pattern = pattern.replace(r"\*", ".*")

        if anchored:
            pattern = f"^{pattern}$"
        else:
            pattern = f"^{pattern}"

        return re.match(pattern, url_path) is not None

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
    
    def is_path_allowed(
        self, url_path: str, rules: list[RobotsRule]
    ) -> bool:
        matches = [
            rule for rule in rules
            if self.rule_matches(rule.path, url_path)
        ]

        if not matches:
            return True

        best = max(
            matches,
            key=lambda rule: (
                len(rule.path.replace("*", "").rstrip("$")),
                rule.allowed,
            ),
        )
        return best.allowed
    
    async def extract_rules(self, url: str) -> list[RobotsGroup]:
        origin = self.derive_origin(url)

        if origin in self.robots_cache:
            return self.robots_cache[origin]

        lock = self.locks.setdefault(origin, asyncio.Lock())

        async with lock:
            if origin in self.robots_cache:
                return self.robots_cache[origin]

            robots_url = self.point_to_root(url)

            try:
                response = await self.client.get(
                    robots_url,
                    follow_redirects=True,
                )
            except httpx.HTTPError:
                # Unreachable robots file: fail closed.
                groups = [RobotsGroup(["*"], [RobotsRule("/", False)])]
                self.robots_cache[origin] = groups
                return groups

            if 400 <= response.status_code < 500:
                '''RFC 9309: an unavailable robots file may be treated
                as permitting access. This includes 429 in this
                simplified policy'''
                groups = []
            elif response.status_code >= 500:
                # Unreachable robots file: fail closed.
                groups = [RobotsGroup(["*"], [RobotsRule("/", False)])]
            else:
                groups = self.parse_rules(response.text)

            self.robots_cache[origin] = groups
            return groups

    async def is_allowed(self, url: str) -> bool:
        self.derive_origin(url)  # validate the url
        path = urlsplit(url).path or "/"
        groups = await self.extract_rules(url)
        rules = self.select_rules(groups)
        return self.is_path_allowed(path, rules)


    # async def extract_rules(self, url:str):
    #     ## cache check
    #     origin = self.derive_origin(url)
    #     if origin in self.robots_cache:
    #         return self.robots_cache[origin]
        
    #     # if no cache, proceed to fetching & parsing robots.txt
        
    #     robots_url = self.point_to_root(url)
    #     res = await self.client.get(robots_url)

    #     if res.text:
    #         rules = res.text.strip()
    #         lines = rules.split('\n')

    #         trans_rules = self.transform_rules(lines)
    #         self.robots_cache[origin] = trans_rules 
    #         return trans_rules
        
    #     return []
    
    # async def is_allowed(self, url:str) -> bool:
    #     # extract path
    #     url_path = urlsplit(url).path

    #     if url_path:
    #         rules = await self.extract_rules(url)
    #         # matching_rules = [rule for rule in rules if path.startswith(rule.path)]
    #         matching_rules = []

    #         for rule in rules:
    #             if self.rule_matches(rule.path, url_path):
    #                 matching_rules.append(rule)
    
    #         if not matching_rules:
    #             print('no matching rules')
    #             return True
            
    #         print('[debug] rules: ', rules)
    #         # best_match = max(
    #         #                 matching_rules,
    #         #                 key=lambda rule: len(rule.path)
    #         #             )
    #         best_match = max(
    #             matching_rules,
    #             key=lambda rule: (
    #                 len(rule.path.rstrip("$").replace("*", "")),
    #                 rule.allowed
    #             )
    #         )
    #         return best_match.allowed
        
        
    #     raise ValueError('path extraction failed for the given URL')

    '''
    Note:-
    Commenting out the fetch parse of the robotparser lib implementation for now
    as it was not as expected to process the robots.txt
    '''

    '''
    The logic:-
    downloads the text, and parses all the Allow, Disallow, and Crawl-delay rules into memory.

    Expected return value from the server:
    User-agent: *
    Disallow: /private/
    Allow: /private/public/
    Crawl-delay: 2

    parser converts these textual directives into rules it can evaluate.

    '''
    # async def fetch_parse(self, url:str):
    #     # self.rp.read(f'{self.point_to_root(self.url)}robots.txt')
    #     org = self.derive_origin(url)
    #     # if not self.robots_cache or (rp.mtime == 0):
    #     if org in self.robots_cache:
    #         return self.robots_cache[org]

    #     robots_url = self.point_to_root(url)
    #     res = await self.client.get(robots_url)
    #     rp = rpt.RobotFileParser()

    #     rp.set_url(robots_url)
    #     print("[debug] the rules: ", res.text.splitlines())
    #     rp.parse(res.text.splitlines())
    #     rp.modified()
    #     print("[debug] Default user agents:", rp.default_entry.useragents)

    #     print('[debug] checking some props:',[(rule.path, rule.allowance, len(rule.path)) for rule in rp.default_entry.rulelines])

    #     print('[debug] checking permissions: ', rp.can_fetch(self.cfg.user_agent, "https://example.com/private/"))
    #     print('[debug] checking permissions for /private/public: ', rp.can_fetch(self.cfg.user_agent, "https://example.com/private/public"))
    #     self.robots_cache[org] = rp

    #     print('[debug] checking the parsed entries: ', f'{rp.entries}\n')
    #     print('[debug] the default entry: ', f'{rp.default_entry}')

            
    #     return rp
    
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

    # async def check(self, url: str) -> bool:
    #     parser = await self.fetch_parse(url)
    #     return parser.can_fetch(self.cfg.user_agent, url)

    #     # rp = self.fetch_parse(url)
    #     # return rp.can_fetch(self.cfg.user_agent, f'{self.derive_origin(url)}')


    


