from typing import Any, AsyncGenerator

from fastapi import APIRouter, BackgroundTasks
from starlette.requests import Request
from starlette.responses import StreamingResponse

from configs.crawl4ai.crawl_rule import browser_config, crawler_config
from controllers.params import CrawlJobPayload, CrawlJobResponse
from libs.deps import CurrentApiKeyDep
from service.crawl4ai_service import Crawl4AIService
from utils.encoders import merge_dicts

router = APIRouter(tags=['crawl'], prefix="/v1")


@router.post("/crawl/job", status_code=202)
async def crawl_job(
        payload: CrawlJobPayload,
        background_tasks: BackgroundTasks,
        current_key: CurrentApiKeyDep
):
    # Use default configs if not provided
    if payload.browser_config is None:
        payload.browser_config = browser_config
    else:
        payload.browser_config = merge_dicts(browser_config, payload.browser_config)
    if payload.crawler_config is None:
        payload.crawler_config = crawler_config
    else:
        payload.crawler_config = merge_dicts(crawler_config, payload.crawler_config)
    return await Crawl4AIService.handle_crawl_job(
        background_tasks,
        [str(u) for u in payload.urls],
        payload.browser_config,
        payload.crawler_config,
        payload.query,
        payload.stream,
        str(payload.notify_url)
    )


@router.post("/crawl/stream/job", response_model=None)
async def crawl_stream_job(
        payload: CrawlJobPayload,
        current_key: CurrentApiKeyDep
) -> Any:
    # Use default configs if not provided
    if payload.browser_config is None:
        payload.browser_config = browser_config
    else:
        payload.browser_config = merge_dicts(browser_config, payload.browser_config)
    if payload.crawler_config is None:
        payload.crawler_config = crawler_config
    else:
        payload.crawler_config = merge_dicts(crawler_config, payload.crawler_config)
    content = await Crawl4AIService.handle_crawl_request([str(u) for u in payload.urls], payload.browser_config,
                                                         payload.crawler_config, payload.query, payload.stream, )
    # result=json.dumps(content).encode('utf-8')
    if not isinstance(content, AsyncGenerator):
        return CrawlJobResponse.model_validate(content)
    else:
        async def event_generator() -> AsyncGenerator[Any, None]:
            yield f"{CrawlJobResponse.model_validate(content)}\n\n"

        return StreamingResponse(content=event_generator(), media_type="text/event-stream")


@router.get("/crawl/job/{task_id}")
async def crawl_job_status(
        request: Request,
        task_id: str,
        current_key: CurrentApiKeyDep
):
    return await Crawl4AIService.handle_task_status(task_id, base_url=str(request.base_url))
