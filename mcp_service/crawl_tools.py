import asyncio
from typing import Any

from pydantic import HttpUrl

from configs.crawl4ai.crawl_rule import browser_config, crawler_config
from controllers.params import CrawlJobPayload, CrawlJobResponse, WebEngineCrawlJobPayload
from libs import mcp_context
from service.crawl4ai_service import Crawl4AIService
from utils.encoders import merge_dicts

mcp= mcp_context.get()

@mcp.tool(name="Provide-URL-based-web-content-crawling", description="Directly crawl and return content from the specified webpage link")
async def crawl_web(
        urls:list[HttpUrl],
)-> Any:
    payload=CrawlJobPayload(urls=urls)
    if payload.browser_config is None:
        payload.browser_config = browser_config
    else:
        payload.browser_config = merge_dicts(browser_config, payload.browser_config)
    if payload.crawler_config is None:
        payload.crawler_config = crawler_config
    else:
        payload.crawler_config = merge_dicts(crawler_config, {'screenshot': False})
        payload.stream =False
    content = await Crawl4AIService.handle_crawl_request([str(u) for u in payload.urls], payload.browser_config,
                                                        payload.crawler_config, payload.query, payload.stream)
    crawl_job_response = CrawlJobResponse.model_validate(content)
    content_list = []
    for item in crawl_job_response.results:
        content_list.append(item.crawl_text)
    return content_list


@mcp.tool(name="search-the-content-from-the-web", description="Search the content from the web using various search engines such as DuckDuckGo, Brave, and Baidu.")
async def web_search(
        web_content:str
)-> Any:
    search_engine_typse = ['duckduckgo', 'brave', 'baidu']
    content_list = []
    async def fetch_content(search_engine: str):
        payload = WebEngineCrawlJobPayload(web_content=web_content, search_engine_type=search_engine)
        content = await Crawl4AIService.handle_web_search_job(payload)
        crawl_job_response = CrawlJobResponse.model_validate(content)
        return [item.crawl_text for item in crawl_job_response.results]

    tasks = [fetch_content(search_engine) for search_engine in search_engine_typse]
    results = await asyncio.gather(*tasks)

    for result in results:
        content_list.extend(result)

    return content_list