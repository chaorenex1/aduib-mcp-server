from fastapi import APIRouter

from .auth import api_key
from .crawl4ai import crawl4ai

api_router = APIRouter()

#auth
api_router.include_router(api_key.router)

#crawl4ai
api_router.include_router(crawl4ai.router)