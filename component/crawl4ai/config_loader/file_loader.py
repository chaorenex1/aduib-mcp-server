import logging
import os

from component.crawl4ai.config_loader.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class FileConfigLoader(ConfigLoader):
    """
    Load configuration from a local file.
    """
    def __init__(self, config_path: str,app_home:str):
        self.app_home = app_home
        self.config_path = config_path

    def load(self) -> str:
        if not os.path.exists(self.config_path):
            logger.warning(f"crawl configuration file {self.config_path} does not exist.")
            if os.path.exists(os.path.join(self.app_home, "crawl_config.json")):
                self.config_path = os.path.join(self.app_home, "crawl_config.json")
            else:
                logger.warning(
                    f"crawl configuration file {self.config_path} does not exist, using default empty config.")
                raise FileNotFoundError(f"crawl configuration file {self.config_path} does not exist.")
        with open(self.config_path, 'rt', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Loaded crawl configuration from {self.config_path}")
        return content