import asyncio
import json
import logging
import time
from base64 import b64encode
from datetime import datetime, timedelta
from functools import partial
from typing import List, Dict, Any
from typing import Optional, AsyncGenerator
from uuid import uuid4

import psutil
from crawl4ai import (
    CrawlerRunConfig,
    CacheMode,
    BrowserConfig,
    MemoryAdaptiveDispatcher,
    RateLimiter
)
from fastapi import HTTPException, status
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse

from component.cache.redis_cache import redis_client as redis
from component.crawl4ai.crawler_pool import get_rule_by_url
from configs import config
from configs.crawl4ai.types import TaskStatus, CrawlRule, CrawlMode, CrawlResultType
from utils import jsonable_encoder

logger = logging.getLogger(__name__)


class Crawl4AIService:

    @classmethod
    def should_cleanup_task(cls, created_at: str, ttl_seconds: int = 3600) -> bool:
        """Check if task should be cleaned up based on creation time."""
        created = datetime.fromisoformat(created_at)
        return (datetime.now() - created).total_seconds() > ttl_seconds

    # --- Helper to get memory ---
    @classmethod
    def _get_memory_mb(cls) -> Optional[float]:
        """Get current process memory usage in MB."""
        try:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not get memory info: {e}")
            return None

    @classmethod
    async def handle_task_status(
            cls,
            task_id: str,
            base_url: str,
            *,
            keep: bool = False
    ) -> JSONResponse:
        """Handle aduib_task status check requests."""
        aduib_task = redis.hgetall(f"aduib_task:{task_id}")
        if not aduib_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="aduib_task not found"
            )

        aduib_task = {k.decode('utf-8'): v.decode('utf-8') for k, v in aduib_task.items()}
        response = cls.create_task_response(aduib_task, task_id, base_url)

        if aduib_task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            if not keep and cls.should_cleanup_task(aduib_task["created_at"]):
                redis.delete(f"aduib_task:{task_id}")

        return JSONResponse(response)

    @classmethod
    def create_task_response(cls, aduib_task: dict, task_id: str, base_url: str) -> dict:
        """Create response for aduib_task status check."""
        response = {
            "task_id": task_id,
            "status": aduib_task["status"],
            "created_at": aduib_task["created_at"],
            "url": aduib_task["url"],
            "_links": {
                "self": {"href": f"{base_url}/llm/{task_id}"},
                "refresh": {"href": f"{base_url}/llm/{task_id}"}
            }
        }

        if aduib_task["status"] == TaskStatus.COMPLETED:
            response["result"] = json.loads(aduib_task["result"])
        elif aduib_task["status"] == TaskStatus.FAILED:
            response["error"] = aduib_task["error"]

        return response

    @classmethod
    async def stream_results(cls, crawl_rule: CrawlRule | None, results_gen: AsyncGenerator) -> AsyncGenerator[
        str, None]:
        """Stream results with heartbeats and completion markers."""
        import json
        def datetime_handler(x):
            if isinstance(x, datetime):
                return x.isoformat()
            raise TypeError("Unknown type")

        try:
            async for result in results_gen:
                try:
                    server_memory_mb = cls._get_memory_mb()
                    result_dict = result.model_dump()
                    result_dict['server_memory_mb'] = server_memory_mb
                    logger.info(f"Streaming result for {result_dict.get('url', 'unknown')}")
                    data = json.dumps(cls.create_processed_result(crawl_rule, result), default=datetime_handler,ensure_ascii=False) + "\n"
                    yield data
                except Exception as e:
                    logger.error(f"Serialization error: {e}")
                    error_response = {"error": str(e), "url": getattr(result, 'url', 'unknown')}
                    yield json.dumps(error_response) + "\n"

        except asyncio.CancelledError:
            logger.warning("Client disconnected during streaming")
        finally:
            # try:
            #     await crawler.close()
            # except Exception as e:
            #     logger.error(f"Crawler cleanup error: {e}")
            pass

    @classmethod
    async def handle_crawl_request(
            cls,
            urls: List[str],
            browser_config: dict,
            crawler_config: dict,
            query: list[str] | str = None,
            stream: bool = False,
            notify_url: str = None
    ) -> None | AsyncGenerator[str, None] | dict[str, bool | list[Any] | float | None | int]:
        """Handle non-streaming crawl requests."""
        start_mem_mb = cls._get_memory_mb()  # <--- Get memory before
        start_time = time.time()
        mem_delta_mb = None
        peak_mem_mb = start_mem_mb

        try:
            urls = [('https://' + url) if not url.startswith(('http://', 'https://')) and not url.startswith(
                ("raw:", "raw://")) else url for url in urls]
            browser_config = BrowserConfig.load(browser_config)
            crawler_config = CrawlerRunConfig.load(crawler_config)
            crawler_config.cache_mode = CacheMode.BYPASS
            crawler_config.stream = stream

            from configs.crawl4ai.crawl_rule import CrawlRules
            crawl_rule = get_rule_by_url(urls[0])
            logger.debug(f"Matched crawl rule: {crawl_rule}")

            if crawl_rule.css_selector:
                crawler_config.css_selector = crawl_rule.css_selector

            markdown_generator = CrawlRule.build_markdown_generator(crawl_rule)
            crawler_config.markdown_generator = markdown_generator

            deep_crawl_strategy = crawl_rule.build_deep_crawl_strategy(query=query)
            crawler_config.deep_crawl_strategy = deep_crawl_strategy

            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=config.MEMORY_THRESHOLD_PRECENT,
                rate_limiter=RateLimiter(
                    base_delay=config.RATE_LIMITER_BASE_DELAY,
                ) if config.RATE_LIMITER_ENABLED else None
            )

            from component.crawl4ai.crawler_pool import get_crawler
            crawler = await get_crawler(browser_config)
            if crawl_rule.crawl_mode == CrawlMode.CLASSIC:
                results = []
                func = getattr(crawler, "arun" if len(urls) == 1 else "arun_many")
                partial_func = partial(func,
                                       urls[0] if len(urls) == 1 else urls,
                                       config=crawler_config,
                                       dispatcher=dispatcher)
                results = await partial_func()

                # await crawler.close()

                end_mem_mb = cls._get_memory_mb()  # <--- Get memory after
                end_time = time.time()

                if start_mem_mb is not None and end_mem_mb is not None:
                    mem_delta_mb = end_mem_mb - start_mem_mb  # <--- Calculate delta
                    peak_mem_mb = max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb)  # <--- Get peak memory
                logger.info(
                    f"Memory usage: Start: {start_mem_mb} MB, End: {end_mem_mb} MB, Delta: {mem_delta_mb} MB, Peak: {peak_mem_mb} MB")

                # Process results to handle PDF bytes
                processed_results = []
                if not isinstance(results, AsyncGenerator):
                    for result in results:
                        processed_results.append(await cls.create_processed_result(crawl_rule, result))
                    return {
                        "success": True,
                        "results": processed_results,
                        "server_processing_time_s": end_time - start_time,
                    }
                else:
                    stream_results = cls.stream_results(crawl_rule=crawl_rule, results_gen=results)

                    return stream_results
            else:  # Adaptive crawl

                adaptive_crawler = crawl_rule.build_adaptive_crawler(crawler)
                processed_results = []
                for url in urls:
                    # View statistics
                    adaptive_crawler.print_stats()
                    result = await adaptive_crawler.digest(url, query)
                    # Get the most relevant content
                    relevant_pages = adaptive_crawler.get_relevant_content(top_k=5)
                    for page in relevant_pages:
                        print(f"- {page['url']} (score: {page['score']:.2f})")
                        result = await cls.handle_crawl_request(
                            urls=urls,
                            browser_config=jsonable_encoder(obj=browser_config),
                            crawler_config=jsonable_encoder(obj=crawler_config),
                            query=query
                        )
                        processed_results.append(result)  # Assuming single URL per call


        except Exception as e:
            logger.error(f"Crawl error: {str(e)}", exc_info=True)
            if 'crawler' in locals():  # Check if crawler was initialized and started
                #  try:
                #      await crawler.close()
                #  except Exception as close_e:
                #       logger.error(f"Error closing crawler during exception handling: {close_e}")
                logger.error(f"Error closing crawler during exception handling: {str(e)}")

            # Measure memory even on error if possible
            end_mem_mb_error = cls._get_memory_mb()
            if start_mem_mb is not None and end_mem_mb_error is not None:
                mem_delta_mb = end_mem_mb_error - start_mem_mb

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=json.dumps({  # Send structured error
                    "error": str(e),
                    "server_memory_delta_mb": mem_delta_mb,
                    "server_peak_memory_mb": max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb_error or 0)
                })
            )

    @classmethod
    async def create_processed_result(cls, crawl_rule: CrawlRule | None, result) -> Any:
        data = None
        result_dict = result.model_dump()
        if crawl_rule.crawler_result_type == CrawlResultType.MARKDOWN:
            if result_dict.get('markdown') is not None and result_dict.get('markdown').get('fit_markdown') is not None:
                data = result_dict['markdown']['fit_markdown']
            elif result_dict.get('markdown') is not None and result_dict.get('markdown').get(
                    'raw_markdown') is not None:
                data = result_dict['markdown']['raw_markdown']
        elif crawl_rule.crawler_result_type == CrawlResultType.PDF:
            if result_dict.get('pdf') is not None:
                data = b64encode(result_dict['pdf']).decode('utf-8')
        else:  # HTML
            if result_dict.get('cleaned_html') is not None:
                data = result_dict['cleaned_html']
            else:
                data = result_dict.get('fit_html')
        return {
            "url": result_dict.get('url', ''),
            "crawl_text": data,
            "crawl_type": CrawlResultType.value_of(crawl_rule.crawler_result_type) if crawl_rule else 'html',
            "crawl_media": result_dict.get('media', {}),
            "screenshot": result_dict.get('screenshot', ''),
            "metadata": result_dict.get('metadata', {}),
        }

    @classmethod
    async def handle_crawl_job(
            cls,
            background_tasks: BackgroundTasks,
            urls: List[str],
            browser_config: Dict,
            crawler_config: Dict,
            query: list[str] | str = None,
            stream: bool = False,
            notify_url: str = None
    ) -> Any:
        """
        Fire-and-forget version of handle_crawl_request.
        Creates a aduib_task in Redis, runs the heavy work in a background aduib_task,
        lets /crawl/job/{task_id} polling fetch the result.
        """
        task_id = f"crawl_{uuid4().hex[:8]}"
        redis.hset(f"aduib_task:{task_id}", mapping={
            "status": TaskStatus.PROCESSING,  # <-- keep enum values consistent
            "created_at": datetime.now().isoformat(),
            "url": json.dumps(urls),  # store list as JSON string
            "result": "",
            "error": "",
        })

        async def _runner():
            try:
                from service.notify import CrawlResultNotifyHandler
                notify_handler = CrawlResultNotifyHandler(urls) if notify_url else None
                result = await cls.handle_crawl_request(
                    urls=urls,
                    browser_config=browser_config,
                    crawler_config=crawler_config,
                    query=query,
                    stream=stream,
                    notify_url=notify_url
                )
                redis.hset(f"aduib_task:{task_id}", mapping={
                    "status": TaskStatus.COMPLETED,
                    "result": json.dumps(result),
                })
                redis.expire(f"aduib_task:{task_id}", timedelta(days=7))
                await notify_handler.notify(result)
                await asyncio.sleep(5)  # Give Redis time to process the update
            except Exception as exc:
                redis.hset(f"aduib_task:{task_id}", mapping={
                    "status": TaskStatus.FAILED,
                    "error": str(exc),
                })

        background_tasks.add_task(_runner)
        return {"task_id": task_id}
