import asyncio
import json

from utils.http import BaseClient


class CrawlResultNotifyHandler:
    """Crawl result notification handler."""

    def __init__(self, urls: list[str]):
        self.urls = urls
        self.client=BaseClient()

    async def notify(self,result):
        """Notify the crawl result."""
        if not result.notify_url:
            return

        async def async_callback():
            try:
                self.client.request(
                    method="POST",
                    path=result.notify_url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(result),
                )
            except Exception:
                pass
        asyncio.create_task(async_callback())