from typing import Any

from pydantic_settings import BaseSettings

from configs.crawl4ai.types import CrawlRuleGroup, CrawlRule
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
    "check_robots_txt":True,
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

class CrawlRules(BaseSettings):
    crawl_rules:list[dict[str,Any]] = [{
        "name": "it_blog",
        "rules": [
            {
                "name": "cnblogs",
                "url": "www.cnblogs.com",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit",
            },
            {
                "name": "csdn",
                "url": "blog.csdn.net",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
                "filter_type":"fit"
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
            },
            {
                "name": "gitlab",
                "url": "gitlab.com",
                "crawl_mode": "classic",
                "crawl_result_type": "markdown",
            }
        ]
    },{
        "name": "search_engine",
        "rules": [
            {
                "name": "baidu",
                "url": "www.baidu.com",
                "crawl_mode": "classic",
                "deep_crawl": "true",
                "deep_crawl_method": "relevance",
            },
            {
                "name": "google",
                "url": "https://www.google.com",
                "crawl_mode": "classic",
                "deep_crawl": "true",
                "deep_crawl_method": "relevance",
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
    def get_rule_by_url(cls, url:str)->CrawlRule |None:
        """Get crawl rule by matching domain name from URL."""
        for group in cls.get_rules():
            for rule in group.rules:
                if rule.url == get_domain_url(url):
                    return rule
        return None
