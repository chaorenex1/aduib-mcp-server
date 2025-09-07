from typing import Dict

from pydantic import HttpUrl, BaseModel


class CrawlJobPayload(BaseModel):
    urls:           list[HttpUrl]
    browser_config: Dict = {}
    crawler_config: Dict = {}
    query: list[str] | str = None
    stream: bool = False
