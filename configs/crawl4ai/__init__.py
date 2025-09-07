from pydantic_settings import BaseSettings

class Crawl4AIConfig(BaseSettings):
    MEMORY_THRESHOLD_PRECENT: float = 80.0  # 80% of memory usage
    IDLE_TTL_SEC: int = 1800  # 30 minutes
    RATE_LIMITER_ENABLED: bool = True
    RATE_LIMITER_BASE_DELAY: tuple= (1.0, 3.0)  # seconds
    CRAWLER_MAX_PAGES: int = 30
    CRAWLER_LLM_BASE_URL: str = "http://localhost:5000"
    CRAWLER_LLM_MODEL: str = "gpt-3.5-turbo"
    CRAWLER_EMBEDDING_MODEL: str = "text-embedding-3-small"
    CRAWLER_API_KEY: str = ""