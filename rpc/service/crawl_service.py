import asyncio
from typing import Any

from aduib_rpc.server.request_excution.service_call import service

from controllers.params import CrawlJobResponse, WebEngineCrawlJobPayload
from service.crawl4ai_service import Crawl4AIService


@service("CrawlService")
class CrawlService:
    """Crawl Service for handling crawl requests."""
    async def crawl(self, urls:list[str],notify_url:str=None) -> dict[str, Any]:
        # Implement crawling logic here
        return await Crawl4AIService.handle_crawl_job(
            urls=urls,
            browser_config={},
            crawler_config={},
            notify_url=notify_url
        )


    async def web_search(self, web_content:str) -> list[str]:
        """Perform web search using multiple search engines concurrently."""
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