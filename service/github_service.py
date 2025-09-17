from configs.crawl4ai.crawl_rule import CrawlRules, browser_config, crawler_config
from configs.crawl4ai.types import CrawlRule
from controllers.params import CrawlJobPayload, CrawlJobResponse
from service.crawl4ai_service import Crawl4AIService
from utils import merge_dicts


class GitHubService:

    @classmethod
    async def search_repositories(cls, repo_name: str= "", code_snippet: str= "", issue_snippet: str= "", pages: int=2) -> str:

        rule:CrawlRule = CrawlRules.get_rule_by_name("git_repo_search", "github")

        type="repositories"
        query = repo_name
        if repo_name and len(repo_name) > 0:
            type="repositories"
            query = repo_name
        elif code_snippet and len(code_snippet) > 0:
            type="code"
            query = code_snippet
        elif issue_snippet and len(issue_snippet) > 0:
            type="issues"
            query = issue_snippet

        urls=[]
        for page in range(1, pages+1):
            search_url = rule.search_engine_url.format(query=query, type=type, page=page)
            urls.append(search_url)

        payload = CrawlJobPayload(urls=urls)
        if payload.browser_config is None:
            payload.browser_config = browser_config
        else:
            payload.browser_config = merge_dicts(browser_config, payload.browser_config)
        if payload.crawler_config is None:
            payload.crawler_config = crawler_config
        else:
            payload.crawler_config = merge_dicts(crawler_config, {'screenshot': False})
            payload.stream = False
        content = await Crawl4AIService.handle_crawl_request([str(u) for u in payload.urls], payload.browser_config,
                                                             payload.crawler_config, payload.query, payload.stream,"git_repo_search")
        crawl_job_response = CrawlJobResponse.model_validate(content)
        content_list = []
        for item in crawl_job_response.results:
            content_list.append(item.crawl_text)
        return content_list
