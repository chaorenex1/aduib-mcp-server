import asyncio
import json
from typing import Callable

from component.crawl4ai.config_loader.config_loader import ConfigLoader
from component.crawl4ai.crawler_pool import change_crawl_rule
from configs.remote.nacos.client import NacosClient


class RemoteConfigLoader(ConfigLoader):
    """ Load configuration from a remote source (e.g., URL or config center). """
    def __init__(self, data_id: str, client:NacosClient, config_callback: Callable[[list[dict]], None] | None=None):
        self.client=client
        self.data_id = data_id
        if config_callback is None:
            config_callback = change_crawl_rule
        self.config_callback = config_callback
        asyncio.run(self.client.register_config_listener(data_id))
        asyncio.run(self.client.add_config_callback(data_id,config_callback))

    def load(self) -> str:
        return json.dumps(asyncio.run(self.client.get_config(self.data_id)))