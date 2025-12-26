from pydantic_settings import BaseSettings

class Crawl4AIConfig(BaseSettings):
    MEMORY_THRESHOLD_PRECENT: float = 80.0  # 80% of memory usage
    SEMAPHORE_COUNT: int = 10  # max concurrent crawlers
    IDLE_TTL_SEC: int = 30*60  # 30 minutes
    RATE_LIMITER_ENABLED: bool = True
    RATE_LIMITER_BASE_DELAY: tuple= (1.0, 3.0)  # seconds
    CRAWLER_MAX_PAGES: int = 30
    CRAWLER_LLM_BASE_URL: str = "http://10.0.0.96:5001/v1/"
    CRAWLER_LLM_MODEL: str = "deepseek-chat"
    CRAWLER_EMBEDDING_MODEL: str = "Qwen3-Embedding-8B"
    CRAWLER_API_KEY: str = "$2b$12$WkC3a0N8gnrq9ipqxzrEn.S8oqxA8J7wU6KZnYAK66Nhy1448/8ka"
    CRAWLER_CONFIG_PATH: str = "nacos://crawl4ai-crawl_rules.json"