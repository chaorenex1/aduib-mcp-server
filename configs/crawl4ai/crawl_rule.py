from typing import Any

from crawl4ai import LLMConfig, LLMExtractionStrategy
from pydantic_settings import BaseSettings

from configs import config
from configs.crawl4ai.types import CrawlRuleGroup, CrawlRule, WebSearchContentExtractionResult
from utils import get_domain_url

browser_config={

        "use_persistent_context":True,
        "browser_mode":"dedicated",
        "text_mode": False,
        "headless": True,
        "enable_stealth": True,
        # "proxy_config": {
        #     "server": "",
        #     "username": "",
        #     "password": "",
        # },
        "user_agent_mode": "random",  # or "custom"
        "user_agent_generator_config": {
            "browsers": ['Chrome', 'Edge','Safari','Mobile Safari','Android'],  # or "mobile"
            "os": ['Windows', 'Mac OS X','Android','iOS'],  # or "linux", "mac", "android", "ios"
            "platforms": ['desktop', 'mobile'],  # or "mobile"
            "min_version": 100.0,
        },
        "extra_args": [],
    }

crawler_config={
    "check_robots_txt":False,
    "screenshot":True,
    "screenshot_wait_for":5.0,
    "locale":"zh-CN",
    "timezone_id":"Asia/Shanghai",
    "process_iframes":True,
    "remove_overlay_elements":True,
    "magic":True,
    "simulate_user":True,
    "override_navigator":True,
    "user_agent_mode": "random",  # or "custom"
    "user_agent_generator_config": {
        "browsers": ['Chrome', 'Edge','Safari','Mobile Safari','Android'],  # or "mobile"
        "os": ['Windows', 'Mac OS X','Android','iOS'],  # or "linux", "mac", "android", "ios"
        "platforms": ['desktop', 'mobile'],  # or "mobile"
        "min_version": 100.0,
    },
}

web_content_llm_extraction_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="hosted_vllm/" + config.CRAWLER_LLM_MODEL, base_url=config.CRAWLER_LLM_BASE_URL,
                         api_token=config.CRAWLER_API_KEY, temperature=0.01),
    schema=WebSearchContentExtractionResult.model_json_schema(),  # Or use model_json_schema()
    extraction_type="schema",
    instruction="extraction: {web_content}",
    chunk_token_threshold=4096,
    overlap_rate=0.0,
    apply_chunking=True,
    input_format="markdown",  # or "html", "fit_markdown"
    extra_args={
        "input_cost_per_token": 0.000421,
        "output_cost_per_token": 0.000520,
        "extra_headers": {
            "User-Agent": config.DEFAULT_USER_AGENT,
            "X-API-KEY": config.CRAWLER_API_KEY
        }
    }
)

class CrawlRules(BaseSettings):
    crawl_rules:list[dict[str,Any]] = [{
        "name": "default",
        "rules": [
            {
                "name": "default",
                "url": "default",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit"
            }
        ]
    },{
        "name": "it_blog",
        "rules": [
            {
                "name": "cnblogs",
                "url": "www.cnblogs.com",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit",
                "extraction_strategy": "web_content"
            },
            {
                "name": "csdn",
                "url": "blog.csdn.net",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit",
                "extraction_strategy": "web_content"
            }
        ]
    }, {
        "name": "git_repo",
        "rules": [
            {
                "name": "github",
                "url": "github.com",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit"
            },
            {
                "name": "gitlab",
                "url": "gitlab.com",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit"
            }
        ]
    },{
        "name": "common_search_engine",
        "rules": [
            {
                "name": "baidu",
                "url": "www.baidu.com",
                "search_engine_url": "https://www.baidu.com/s?wd={query}",
                "crawl_mode": "classic",
                "deep_crawl": "false",
                "crawl_result_type": "html",
                "filter_type": "fit",
                "deep_crawl_method": "relevance",
                "deep_crawl_max_depth":1,
                "deep_crawl_max_pages":2,
                "extraction_strategy": "web_search"
            },
            {
                "name": "google",
                "url": "www.google.com",
                "search_engine_url": "https://www.google.com/search?q={query}",
                "crawl_mode": "classic",
                "crawl_result_type": "html",
                "filter_type": "fit",
                "deep_crawl": "false",
                "deep_crawl_method": "relevance",
                "deep_crawl_max_depth": 1,
                "deep_crawl_max_pages": 2,
                "extraction_strategy": "web_search"
            },
            {
                "name": "bing",
                "url": "www.bing.com",
                "search_engine_url": "https://www.bing.com/search?q={query}",
                "crawl_mode": "classic",
                "deep_crawl": "false",
                "crawl_result_type": "html",
                "filter_type": "fit",
                "deep_crawl_method": "relevance",
                "deep_crawl_max_depth": 1,
                "deep_crawl_max_pages": 2,
                "extraction_strategy": "web_search"
            },
            {
                "name": "brave",
                "url": "search.brave.com",
                "search_engine_url": "https://search.brave.com/search?q={query}",
                "crawl_mode": "classic",
                "crawl_result_type": "html",
                "filter_type": "fit",
                "deep_crawl": "false",
                "deep_crawl_method": "relevance",
                "deep_crawl_max_depth": 1,
                "deep_crawl_max_pages": 2,
                "extraction_strategy": "web_search"
            },
            {
                "name": "yandex",
                "url": "yandex.com",
                "search_engine_url": "https://yandex.com/search/?text={query}",
                "crawl_mode": "classic",
                "crawl_result_type": "html",
                "filter_type": "fit",
                "deep_crawl": "false",
                "deep_crawl_method": "relevance",
                "deep_crawl_max_depth": 1,
                "deep_crawl_max_pages": 2,
                "extraction_strategy": "web_search"
            }
        ]
    }
]

    @classmethod
    def get_rules(cls)->list[CrawlRuleGroup]:
        """Get all crawl rules."""
        return [CrawlRuleGroup.model_validate(r) for r in cls().crawl_rules]

    @classmethod
    def get_rule_by_name(cls, group_name:str, rule_name:str)->CrawlRule |None:
        """Get crawl rule by group name and rule name."""
        for group in cls.get_rules():
            if group.name == group_name:
                for rule in group.rules:
                    if rule.name == rule_name:
                        return rule
        return None

    @classmethod
    def get_rules_by_group(cls, group_name:str)->CrawlRuleGroup |None:
        """Get crawl rule group by group name."""
        for group in cls.get_rules():
            if group.name == group_name:
                return group
        return None

    @classmethod
    def get_rule_by_url(cls, url:str)->CrawlRule |None:
        """Get crawl rule by matching domain name from URL."""
        for group in cls.get_rules():
            for rule in group.rules:
                if rule.url == get_domain_url(url):
                    return rule
        return None
