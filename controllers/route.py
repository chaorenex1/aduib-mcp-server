from fastapi import APIRouter

from .auth import api_key
from .crawl4ai import crawl4ai
from .crawl4ai import search_engine

api_router = APIRouter()

#auth
api_router.include_router(api_key.router)

#crawl4ai
api_router.include_router(crawl4ai.router)

#web_search
api_router.include_router(search_engine.router)