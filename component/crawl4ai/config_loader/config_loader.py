from abc import ABC, abstractmethod


class ConfigLoader(ABC):
    """Abstract base class for configuration loaders."""

    @abstractmethod
    def load(self) -> str:
        """Load configuration and return as a string."""
        ...

    @classmethod
    def get_config_loader(cls,config_path: str,app_home:str) -> 'ConfigLoader':
        """Factory function to get the appropriate ConfigLoader based on the config_path."""
        from configs import config
        from component.crawl4ai.config_loader.file_loader import FileConfigLoader
        from component.crawl4ai.config_loader.remote_config_loader import RemoteConfigLoader

        if config_path.startswith("nacos://"):
            # Extract data_id from the URL
            data_id = config_path[len("nacos://"):]
            from configs.remote.nacos.client import NacosClient
            client = NacosClient(server_addr=config.NACOS_SERVER_ADDR,
                                 namespace=config.NACOS_NAMESPACE,
                                 user_name=config.NACOS_USERNAME,
                                 group="aduib-mcp-server",
                                 password=config.NACOS_PASSWORD)
            return RemoteConfigLoader(data_id, client,)
        else:
            return FileConfigLoader(config_path,app_home)