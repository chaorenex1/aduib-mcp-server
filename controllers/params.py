from typing import Dict, Any

from pydantic import HttpUrl, BaseModel


class CrawlJobPayload(BaseModel):
    urls:           list[HttpUrl]
    browser_config: Dict = {}
    crawler_config: Dict = {}
    query: list[str] | str = None
    stream: bool = False
    notify_url: HttpUrl = None

class CrawlJobBody(BaseModel):
    url:str
    crawl_text:str
    crawl_type:str
    crawl_media:Dict[str,Any]=None
    screenshot:str=None,
    metadata:Dict = {}

class CrawlJobResponse(BaseModel):
    success:bool
    results: list[CrawlJobBody]
    server_processing_time_s:float=None



class ToolCrawlJobUrlPayload(BaseModel):
    urls:           list[HttpUrl]


class ToolCrawlJobQueryPayload(BaseModel):
    urls:           list[HttpUrl]
    query: list[str] | str = None


class WebEngineCrawlJobPayload(BaseModel):
    web_content:str
    search_engine_type:str='duckduckgo'  # 'google' or 'bing' or 'baidu'

