from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Config:
    concurrency: int = 3 ## maximum allowed simultaneous fetch operations
    requests_per_sec_per_host: float = 10.0
    timeout_secs: float = 10.0 ## HTTP request timeout
    max_attempts: int = 4 ## maximum fetch attempts
    user_agent: str = "ProdAsyncFetcher/0.1" # identifies crawler to servers
    