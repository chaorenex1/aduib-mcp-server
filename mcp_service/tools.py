from typing import Any

from pydantic import HttpUrl

from configs.crawl4ai.crawl_rule import browser_config, crawler_config
from controllers.params import CrawlJobPayload, CrawlJobResponse
from libs import mcp_context
from service.crawl4ai_service import Crawl4AIService
from utils.encoders import merge_dicts

mcp= mcp_context.get()

@mcp.tool(name="爬取网页内容", description="爬取网页内容并返回结果")
async def crawl_stream_job(
        urls:list[HttpUrl],
        query: list[str] | str = None,
)-> Any:
    payload=CrawlJobPayload(urls=urls, query=query)
    if payload.browser_config is None:
        payload.browser_config = browser_config
    else:
        payload.browser_config = merge_dicts(browser_config, payload.browser_config)
    if payload.crawler_config is None:
        payload.crawler_config = crawler_config
    else:
        payload.crawler_config = merge_dicts(crawler_config, payload.crawler_config)
        payload.stream =False
    content = await Crawl4AIService.handle_crawl_request([str(u) for u in payload.urls], payload.browser_config,
                                                        payload.crawler_config, payload.query, payload.stream)
    crawl_job_response = CrawlJobResponse.model_validate(content)
    content_list = []
    for item in crawl_job_response.results:
        content_list.append(item.crawl_text)
    return content_list