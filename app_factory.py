import asyncio
import contextlib
import logging
import os
import pathlib
import time
from typing import AsyncIterator

from aduib_rpc.utils.net_utils import NetUtils
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
        app.app_home = os.getenv("user.home", str(pathlib.Path.home())) + f"/.{config.APP_NAME.lower()}"
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
    from component.crawl4ai.crawler_pool import init_crawler_env
    init_crawler_env()

async def run_service_register(app: AduibAIApp):
    registry_config = {
        "server_addresses": app.config.NACOS_SERVER_ADDR,
        "namespace": app.config.NACOS_NAMESPACE,
        "group_name": app.config.NACOS_GROUP,
        "username": app.config.NACOS_USERNAME,
        "password": app.config.NACOS_PASSWORD,
        "DISCOVERY_SERVICE_ENABLED": app.config.DISCOVERY_SERVICE_ENABLED,
        "DISCOVERY_SERVICE_TYPE": app.config.DISCOVERY_SERVICE_TYPE,
        "SERVICE_TRANSPORT_SCHEME": app.config.SERVICE_TRANSPORT_SCHEME,
        "APP_NAME": app.config.APP_NAME+f"-{app.config.SERVICE_TRANSPORT_SCHEME}",
    }
    from aduib_rpc.server.request_excution.service_call import load_service_plugins
    from aduib_rpc.discover.registry.registry_factory import ServiceRegistryFactory
    from aduib_rpc.discover.service import AduibServiceFactory
    service = await ServiceRegistryFactory.start_service_registry(registry_config)
    service.port=6002
    if service and config.DOCKER_ENV:
        service.host=config.APP_HOST
    factory = AduibServiceFactory(service_instance=service)
    load_service_plugins('rpc.service')
    await factory.run_server()


@contextlib.asynccontextmanager
async def lifespan(app: AduibAIApp) -> AsyncIterator[None]:
    log.info("Lifespan is starting")
    #服务注册
    asyncio.create_task(run_service_register(app))
    from component.crawl4ai.crawler_pool import close_all, janitor
    # --- 初始化 ---
    # 预热 crawler
    from component.crawl4ai.crawler_pool import get_crawler
    from crawl4ai import BrowserConfig
    from configs.crawl4ai.crawl_rule import browser_config
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
