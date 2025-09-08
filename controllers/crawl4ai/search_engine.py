from fastapi import APIRouter

from controllers.params import WebEngineCrawlJobPayload
from libs.deps import CurrentApiKeyDep
from service.crawl4ai_service import Crawl4AIService

router = APIRouter(tags=['web_search'], prefix="/v1")


@router.post("/web_search")
async def web_search_job(
        payload: WebEngineCrawlJobPayload,
        current_key: CurrentApiKeyDep
):
    return await Crawl4AIService.handle_web_search_job(
        payload
    )
