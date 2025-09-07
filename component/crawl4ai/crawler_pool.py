import asyncio
import hashlib
import json
import logging
import subprocess
import time
import traceback
from typing import Dict

import psutil
from crawl4ai import AsyncWebCrawler, BrowserConfig, UndetectedAdapter, AsyncLogger
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from patchright.async_api import BrowserContext, Page

from configs import config
from configs.crawl4ai.crawl_rule import CrawlRules
from configs.crawl4ai.types import CrawlRuleGroup, CrawlRule
from utils import get_domain_url

POOL: Dict[str, AsyncWebCrawler] = {}
LAST_USED: Dict[str, float] = {}
LOCK = asyncio.Lock()
CRAWL_RULES:list[CrawlRuleGroup]=[]

logger=logging.getLogger(__name__)

def install_browsers_if_needed():
    try:
        subprocess.check_call(["playwright", "install", "--with-deps"])
    except FileNotFoundError:
        logger.error("Playwright CLI 未找到，请先安装 Python 包。")

def init_crawler_env():
    from component.crawl4ai.config_loader.config_loader import ConfigLoader
    from libs import app_context
    app = app_context.get()
    try:
        data_dict = ConfigLoader.get_config_loader(config.CRAWLER_CONFIG_PATH, app.app_home).load()
    except Exception:
        data_dict = None
    if data_dict is None:
        for r in CrawlRules().crawl_rules:
            CRAWL_RULES.append(CrawlRuleGroup.model_validate(r))
    else:
        for r in json.loads(data_dict):
            try:
                CRAWL_RULES.append(CrawlRuleGroup.model_validate(r))
            except Exception as e:
                logger.error(f"Invalid crawl rule config: {r}, error: {e}")

def get_rule_by_url(url:str)->CrawlRule |None:
    """Get crawl rule by matching domain name from URL."""
    for group in CRAWL_RULES:
        for rule in group.rules:
            if rule.url == get_domain_url(url):
                return rule
    return None

def change_crawl_rule(new_rules:list[dict]):
    """Change the current crawl rules to new ones."""
    global CRAWL_RULES
    CRAWL_RULES.clear()
    for r in new_rules:
        try:
            CRAWL_RULES.append(CrawlRuleGroup.model_validate(r))
        except Exception as e:
            logger.error(f"Invalid crawl rule config: {r}, error: {e}")


async def on_browser_created(browser, **kwargs):
    # Called once the browser instance is created (but no pages or contexts yet)
    logger.debug("[HOOK] on_browser_created - Browser created successfully!")
    # browser.set_default_timeout(config.BROWSER_DEFAULT_TIMEOUT_MS)
    return browser

async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
    # Called right after a new page + context are created (ideal for auth or route config).
    logger.debug("[HOOK] on_page_context_created - Setting up page & context.")

    # await context.add_init_script(script=load_js_script("auto_toggle"))
    # await context.add_init_script(script=load_js_script("auto_toggle2"))
    # await context.add_init_script(script=load_js_script("auto_toggle3"))
    return page

async def before_goto(
        page: Page, context: BrowserContext, url: str, **kwargs
):
    # Called before navigating to each URL.
    logger.debug(f"[HOOK] before_goto - About to navigate: {url}")
    # e.g., inject custom headers
    # await page.set_extra_http_headers({
    #     "Custom-Header": "my-value"
    # })
    # load_js_script("auto_toggle")
    # load_js_script("auto_toggle2")
    # load_js_script("auto_toggle3")
    # await page.add_script_tag(url="https://update.greasyfork.org/scripts/378351/%E3%80%8CCSDNGreener%E3%80%8D%F0%9F%8D%83CSDN%E5%B9%BF%E5%91%8A%E5%AE%8C%E5%85%A8%E8%BF%87%E6%BB%A4%7C%E5%85%8D%E7%99%BB%E5%BD%95%7C%E4%B8%AA%E6%80%A7%E5%8C%96%E6%8E%92%E7%89%88%7C%E6%9C%80%E5%BC%BA%E8%80%81%E7%89%8C%E8%84%9A%E6%9C%AC%7C%E6%8C%81%E7%BB%AD%E6%9B%B4%E6%96%B0.user.js")
    # await page.add_script_tag(url="https://update.greasyfork.org/scripts/440400/%E8%87%AA%E5%8A%A8%E5%B1%95%E5%BC%80%E5%85%A8%E6%96%87%E9%98%85%E8%AF%BB%E6%9B%B4%E5%A4%9A.user.js")
    # await page.add_script_tag(url="https://update.greasyfork.org/scripts/438656/%E8%87%AA%E5%8A%A8%E5%B1%95%E5%BC%80.user.js")
    return page

async def after_goto(
        page: Page, context: BrowserContext,
        url: str, response, **kwargs
):
    # Called after navigation completes.
    logger.debug(f"[HOOK] after_goto - Successfully loaded: {url}")
    # e.g., wait for a certain element if we want to verify
    try:
        await page.wait_for_selector('.content', timeout=1000)
        logger.debug("[HOOK] Found .content element!")
    except:
        logger.debug("[HOOK] .content not found, continuing anyway.")
    return page

async def on_user_agent_updated(
        page: Page, context: BrowserContext,
        user_agent: str, **kwargs
):
    # Called whenever the user agent updates.
    logger.debug(f"[HOOK] on_user_agent_updated - New user agent: {user_agent}")
    return page

async def on_execution_started(page: Page, context: BrowserContext, **kwargs):
    # Called after custom JavaScript execution begins.
    logger.debug("[HOOK] on_execution_started - JS code is running!")
    return page

async def before_retrieve_html(page: Page, context: BrowserContext, **kwargs):
    # Called before final HTML retrieval.
    logger.debug("[HOOK] before_retrieve_html - We can do final actions")
    # Example: Scroll again
    # await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    return page

async def before_return_html(
        page: Page, context: BrowserContext, html: str, **kwargs
):
    # Called just before returning the HTML in the result.
    logger.debug(f"[HOOK] before_return_html - HTML length: {len(html)}")
    return page

def _sig(cfg: BrowserConfig) -> str:
    payload = json.dumps(cfg.dump(), sort_keys=True, separators=(",",":"))
    return hashlib.sha1(payload.encode()).hexdigest()

async def get_crawler(cfg: BrowserConfig) -> AsyncWebCrawler:
    sig=None
    try:
        sig = _sig(cfg)
        logger.debug(f"Getting crawler with signature: {sig}")
        crawler_logger = AsyncLogger()
        async with LOCK:
            if sig in POOL:
                LAST_USED[sig] = time.time();
                return POOL[sig]
            if psutil.virtual_memory().percent >= config.MEMORY_THRESHOLD_PRECENT:
                raise MemoryError("RAM pressure – new browser denied")
            if cfg.enable_stealth:
                undetected_adapter = UndetectedAdapter()
                # Create the crawler strategy with undetected adapter
                crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                    browser_config=cfg,
                    browser_adapter=undetected_adapter if not cfg.enable_stealth else None,
                    logger=crawler_logger
                )
                crawler_strategy.set_hook("on_browser_created", on_browser_created)
                crawler_strategy.set_hook(
                    "on_page_context_created", on_page_context_created
                )
                crawler_strategy.set_hook("before_goto", before_goto)
                crawler_strategy.set_hook("after_goto", after_goto)
                crawler_strategy.set_hook(
                    "on_user_agent_updated", on_user_agent_updated
                )
                crawler_strategy.set_hook(
                    "on_execution_started", on_execution_started
                )
                crawler_strategy.set_hook(
                    "before_retrieve_html", before_retrieve_html
                )
                crawler_strategy.set_hook(
                    "before_return_html", before_return_html
                )
            crawler = AsyncWebCrawler(config=cfg, thread_safe=False,crawler_strategy=crawler_strategy,logger=crawler_logger)
            await crawler.start()
            POOL[sig] = crawler; LAST_USED[sig] = time.time()
            return crawler
    except MemoryError as e:
        raise MemoryError(f"RAM pressure – new browser denied: {e}")
    except Exception as e:
        traceback.print_exc()
        install_browsers_if_needed()
        logger.error(f"Failed to start browser, please check if the browser is installed properly: {e}")
        # raise RuntimeError(f"Failed to start browser: {e}")
    finally:
        if sig in POOL:
            LAST_USED[sig] = time.time()
        else:
            # If we failed to start the browser, we should remove it from the pool
            POOL.pop(sig, None)
            LAST_USED.pop(sig, None)
        # If we failed to start the browser, we should remove it from the pool
async def close_all():
    async with LOCK:
        await asyncio.gather(*(c.close() for c in POOL.values()), return_exceptions=True)
        POOL.clear(); LAST_USED.clear()

async def janitor():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        async with LOCK:
            for sig, crawler in list(POOL.items()):
                if now - LAST_USED[sig] > config.IDLE_TTL_SEC:
                    from contextlib import suppress
                    with suppress(Exception): await crawler.close()
                    POOL.pop(sig, None); LAST_USED.pop(sig, None)