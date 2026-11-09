from enum import StrEnum, auto
from pydantic import BaseModel

from datetime import datetime

class Status(StrEnum):
    OK = auto()
    HTTP_ERROR = auto()
    NETWORK_ERROR = auto()
    BLOCKED_BY_ROBOTS = auto()
    NOT_HTML = auto()

class Page(BaseModel):
    url: str
    attempts: int
    fetched_et: datetime
    status: Status
    title: str | None = None
    text: str | None = None
    word_count: int | None = None
    

