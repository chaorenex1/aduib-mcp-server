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
from libs.exception_middleware import GlobalExceptionMiddleware, CircuitBreakerMiddleware

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

    # Global exception handling (outermost - catches all)
    app.add_middleware(GlobalExceptionMiddleware)
    # Circuit breaker (opens after 10 failures, resets after 60s)
    app.add_middleware(CircuitBreakerMiddleware, failure_threshold=10, reset_timeout=60.0)

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
    from aduib_rpc.discover.registry.registry_factory import ServiceRegistryFactory
    from aduib_rpc.discover.entities import ServiceInstance
    from aduib_rpc.utils.constant import AIProtocols
    from aduib_rpc.utils.constant import TransportSchemes
    from aduib_rpc.discover.service import AduibServiceFactory
    from aduib_rpc.server.rpc_execution.service_call import load_service_plugins
    ip, port = NetUtils.get_ip_and_free_port()
    service_registry = ServiceRegistryFactory.start_service_discovery(registry_config)
    service_info = ServiceInstance(service_name=registry_config.get('APP_NAME', 'aduib-rpc'), host=ip, port=port,
                                       protocol=AIProtocols.AduibRpc, weight=1,
                                       scheme=config.SERVICE_TRANSPORT_SCHEME or TransportSchemes.GRPC)
    if service_info and config.RPC_SERVICE_PORT>0:
        service_info.port=config.RPC_SERVICE_PORT

    factory = AduibServiceFactory(service_instance=service_info)
    load_service_plugins('rpc.service')
    load_service_plugins('rpc.client')
    if service_info and config.DOCKER_ENV:
        new_service_info = ServiceInstance(service_name=service_info.service_name, host=config.RPC_SERVICE_HOST, port=service_info.port,
                                       protocol=service_info.protocol, weight=service_info.weight,
                                       scheme=service_info.scheme)
        await service_registry.register_service(new_service_info)
    else:
        await service_registry.register_service(service_info)
    await factory.run_server()


@contextlib.asynccontextmanager
async def lifespan(app: AduibAIApp) -> AsyncIterator[None]:
    log.info("Lifespan is starting")
    #服务注册
    asyncio.create_task(run_service_register(app))
    # --- 初始化 ---
    # 预热 crawler
    from component.crawl4ai.crawler_pool import get_crawler, janitor, close_all
    from crawl4ai import BrowserConfig
    from configs.crawl4ai.crawl_rule import browser_config
    await get_crawler(BrowserConfig.load(browser_config))

    # 开启 janitor 清理闲置浏览器
    janitor_task = asyncio.create_task(janitor())
    janitor_task.add_done_callback(
        lambda t: log.error(f"Janitor task crashed: {t.exception()}")
        if t.exception() else None
    )
    app.state.janitor = janitor_task

    # 如果是 streamable-http 模式，开启 session_manager
    session_manager = None
    if config.TRANSPORT_TYPE == "streamable-http":
        from mcp_factory import get_mcp
        session_manager = get_mcp().session_manager

    # Session Manager 恢复配置
    MAX_SESSION_RETRIES = 3
    RETRY_BACKOFF_BASE = 2

    if session_manager:
        last_error = None
        for attempt in range(MAX_SESSION_RETRIES):
            try:
                async with session_manager.run():
                    yield
                    return
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_error = e
                log.error(
                    f"Session manager error (attempt {attempt + 1}/{MAX_SESSION_RETRIES}): {e}",
                    exc_info=True,
                )
                if attempt < MAX_SESSION_RETRIES - 1:
                    backoff = RETRY_BACKOFF_BASE ** attempt
                    log.info(f"Retrying session manager in {backoff}s...")
                    await asyncio.sleep(backoff)

        log.critical(
            f"Session manager failed after {MAX_SESSION_RETRIES} attempts, running in degraded mode"
        )
        yield
    else:
        yield

    # --- 清理 ---
    if hasattr(app.state, 'janitor') and app.state.janitor:
        app.state.janitor.cancel()
    await close_all()
