from enum import StrEnum, Enum

from crawl4ai import KeywordRelevanceScorer, BestFirstCrawlingStrategy, BFSDeepCrawlStrategy, FilterChain, SEOFilter, \
    DeepCrawlStrategy, BM25ContentFilter, PruningContentFilter, LLMContentFilter, \
    DefaultMarkdownGenerator, AdaptiveCrawler, AsyncWebCrawler, AdaptiveConfig, LLMConfig
from crawl4ai.deep_crawling import ContentRelevanceFilter
from pydantic import BaseModel

from configs import config


class TaskStatus(str, Enum):
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"


class FilterType(str, Enum):
    RAW = "raw"
    FIT = "fit"
    BM25 = "bm25"
    LLM = "llm"


class CrawlMode(StrEnum):
    CLASSIC = "classic"
    ADAPTIVE = "adaptive"

    @classmethod
    def to_original(cls, value: str) -> 'CrawlMode':
        match value.lower():
            case "classic":
                return cls.CLASSIC
            case "adaptive":
                return cls.ADAPTIVE
            case _:
                raise ValueError(f"Unknown crawl mode: {value}")

    @classmethod
    def value_of(cls, value: 'CrawlMode') -> str:
        match value:
            case cls.CLASSIC:
                return "classic"
            case cls.ADAPTIVE:
                return "adaptive"
            case _:
                raise ValueError(f"Unknown crawl mode: {value}")


class CrawlResultType(StrEnum):
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"

    @classmethod
    def to_original(cls, value: str) -> 'CrawlResultType':
        match value.lower():
            case "html":
                return cls.HTML
            case "markdown":
                return cls.MARKDOWN
            case "pdf":
                return cls.PDF
            case _:
                raise ValueError(f"Unknown crawl type: {value}")

    @classmethod
    def value_of(cls, value: 'CrawlResultType') -> str:
        match value:
            case cls.HTML:
                return "html"
            case cls.MARKDOWN:
                return "markdown"
            case cls.PDF:
                return "pdf"
            case _:
                raise ValueError(f"Unknown crawl type: {value}")


class CrawlRule(BaseModel):
    name: str
    url: str
    crawl_mode: CrawlMode = CrawlMode.CLASSIC
    adaptive_crawl_method: str = "statistical"  # 'statistical' or 'embedding'
    crawler_result_type: CrawlResultType = CrawlResultType.MARKDOWN
    css_selector: str = None
    filter_type: FilterType = FilterType.RAW
    deep_crawl: bool = False
    deep_crawl_method: str = None  # 'seo' or 'keyword' or 'relevance'
    deep_crawl_max_depth: int = 2
    deep_crawl_threshold: float = 0.7

    def build_deep_crawl_strategy(self, query: list[str] | str = None) -> DeepCrawlStrategy|None:
        """Build the deep crawl strategy based on the rule settings."""
        match self.deep_crawl_method:
            case "seo":
                return BFSDeepCrawlStrategy(max_depth=self.deep_crawl_max_depth,
                                            filter_chain=FilterChain(filters=[
                                                SEOFilter(threshold=self.deep_crawl_threshold, keywords=query)]))
            case "keyword":
                return BestFirstCrawlingStrategy(max_depth=self.deep_crawl_max_depth,
                                                 url_scorer=KeywordRelevanceScorer(keywords=query,
                                                                                   weight=self.deep_crawl_threshold))
            case "relevance":
                return BFSDeepCrawlStrategy(max_depth=self.deep_crawl_max_depth,
                                            filter_chain=FilterChain(filters=[
                                                ContentRelevanceFilter(threshold=self.deep_crawl_threshold,
                                                                       query=query)]))
            case _:
                return None

    def build_markdown_generator(self, query: list[str] | str = None) -> DefaultMarkdownGenerator | None:
        """Build the adaptive crawl filter based on the rule settings."""
        match self.filter_type:
            case FilterType.RAW:
                return DefaultMarkdownGenerator()
            case FilterType.FIT:
                return DefaultMarkdownGenerator(content_filter=PruningContentFilter(user_query=query))
            case FilterType.BM25:
                return DefaultMarkdownGenerator(content_filter=BM25ContentFilter(user_query=query, use_stemming=False))
            case FilterType.LLM:
                return DefaultMarkdownGenerator(content_filter=LLMContentFilter(
                    llm_config=LLMConfig(provider="openai/"+config.CRAWLER_LLM_MODEL,base_url=config.CRAWLER_LLM_BASE_URL,api_token=config.CRAWLER_API_KEY,top_p=1.0,temperature=0.01),
                    # or use environment variable
                    instruction="""
                        Focus on extracting the core educational content.
                        Include:
                        - Key concepts and explanations
                        - Important code examples
                        - Essential technical details
                        Exclude:
                        - Navigation elements
                        - Sidebars
                        - Footer content
                        Format the output as clean markdown with proper code blocks and headers.
                        """,
                    chunk_token_threshold=4096,  # Adjust based on your needs
                    verbose=True,
                    extra_args={
                        "extra_headers": {
                            "User-Agent": config.DEFAULT_USER_AGENT,
                            "X-API-KEY": config.CRAWLER_API_KEY
                        }
                    }
                )
                )
            case _:
                return None

    def build_adaptive_crawler(self, crawler: AsyncWebCrawler) -> AdaptiveCrawler | None:
        """Build the adaptive crawler based on the rule settings."""
        match self.adaptive_crawl_method:
            case "statistical":
                return AdaptiveCrawler(crawler=crawler,
                                       config=AdaptiveConfig(strategy="statistical", confidence_threshold=0.8,top_k_links=5,max_depth=2,max_pages=10))
            case "embedding":
                return AdaptiveCrawler(crawler=crawler,
                                       config=AdaptiveConfig(strategy="embedding",confidence_threshold=0.8,top_k_links=5,max_depth=2,max_pages=10, embedding_llm_config={
                                           "base_url": config.CRAWLER_LLM_BASE_URL,
                                           "model": config.CRAWLER_EMBEDDING_MODEL,
                                           "api_key": config.CRAWLER_API_KEY,
                                       })
                                       )
            case _:
                return None


class CrawlRuleGroup(BaseModel):
    name: str
    rules: list[CrawlRule] = []

    @classmethod
    def get_rules_by_name(cls, groups: list['CrawlRuleGroup'], name: str) -> list[CrawlRule]:
        for group in groups:
            if group.name == name:
                return group.rules
        return []
