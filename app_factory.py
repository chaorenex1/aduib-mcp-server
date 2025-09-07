import asyncio
import contextlib
import logging
import os
import pathlib
import time
from typing import AsyncIterator

from fastapi.routing import APIRoute
from starlette.staticfiles import StaticFiles

from aduib_app import AduibAIApp
from component.cache.redis_cache import init_cache
from component.log.app_logging import init_logging
from configs import config
from controllers.route import api_router
from libs.context import LoggingMiddleware, TraceIdContextMiddleware, ApiKeyContextMiddleware

log=logging.getLogger(__name__)


def create_app_with_configs()->AduibAIApp:
    """ Create the FastAPI app with necessary configurations and middlewares.
    :return: AduibAIApp instance
    """

    from libs import app_context
    if app_context.get():
        return app_context.get()
    def custom_generate_unique_id(route: APIRoute) -> str:
        return f"{route.tags[0]}-{route.name}"

    app = AduibAIApp(
        title=config.APP_NAME,
        generate_unique_id_function=custom_generate_unique_id,
        debug=config.DEBUG,
        lifespan=lifespan,
    )
    app.config=config
    if config.APP_HOME:
        app.app_home = config.APP_HOME
    else:
        app.app_home = os.getcwd()
    app.include_router(api_router)
    if config.AUTH_ENABLED:
        app.add_middleware(ApiKeyContextMiddleware)
    if config.DEBUG:
        log.warning("Running in debug mode, this is not recommended for production use.")
        app.add_middleware(LoggingMiddleware)
    app.add_middleware(TraceIdContextMiddleware)
    app_context.set(app)
    return app


def create_app()->AduibAIApp:
    start_time = time.perf_counter()
    app = create_app_with_configs()
    init_logging(app)
    init_apps(app)
    end_time = time.perf_counter()
    log.info(f"App home directory: {app.app_home}")
    log.info(f"Finished create_app ({round((end_time - start_time) * 1000, 2)} ms)")
    return app


def init_apps(app: AduibAIApp):
    """
    Initialize the app with necessary configurations and middlewares.
    :param app: AduibAIApp instance
    """
    log.info("Initializing middlewares")
    init_cache(app)
    log.info("middlewares initialized successfully")

def init_crawler_pool(app: AduibAIApp):
    MAX_PAGES = config.CRAWLER_MAX_PAGES
    GLOBAL_SEM = asyncio.Semaphore(MAX_PAGES)
    from crawl4ai import AsyncWebCrawler
    orig_arun = AsyncWebCrawler.arun

    async def capped_arun(self, *a, **kw):
        async with GLOBAL_SEM:
            return await orig_arun(self, *a, **kw)

    AsyncWebCrawler.arun = capped_arun

    # ── static playground ──────────────────────────────────────
    STATIC_DIR = pathlib.Path(__file__).parent / "static" / "playground"
    if not STATIC_DIR.exists():
        raise RuntimeError(f"Playground assets not found at {STATIC_DIR}")
    app.mount(
        "/playground",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="play",
    )


@contextlib.asynccontextmanager
async def lifespan(app: AduibAIApp) -> AsyncIterator[None]:
    log.info("Lifespan is starting")
    from configs.crawl4ai.crawl_rule import browser_config
    from component.crawl4ai.crawler_pool import close_all, get_crawler, BrowserConfig, janitor
    # --- 初始化 ---
    # 预热 crawler
    await get_crawler(BrowserConfig.load(browser_config))

    # 开启 janitor
    app.state.janitor = asyncio.create_task(janitor())

    # 如果是 streamable-http 模式，开启 session_manager
    session_manager = None
    if config.TRANSPORT_TYPE == "streamable-http":
        session_manager = app.mcp.session_manager

    if session_manager:
        async with session_manager.run():
            yield
    else:
        yield

    # --- 清理 ---
    app.state.janitor.cancel()
    await close_all()
