import logging
import os

from configs import config
from fast_mcp import FastMCP

log=logging.getLogger(__name__)

class MCPFactory:
    """ Factory class to create and manage FastMCP instances."""
    def __init__(self):
        self.mcp = self.init_fast_mcp()

    def get_mcp(self)->FastMCP:
        return self.mcp

    @classmethod
    def get_mcp_factory(cls)->'MCPFactory':
        return cls()

    def init_fast_mcp(self)->FastMCP:
        mcp= None
        if not config.DISCOVERY_SERVICE_ENABLED:
            from fast_mcp import FastMCP
            mcp = FastMCP(name=config.APP_NAME,instructions=config.APP_DESCRIPTION,version=config.APP_VERSION,auth_server_provider=None)
        else:
            if config.DISCOVERY_SERVICE_TYPE=="nacos":
                from nacos_mcp_wrapper.server.nacos_settings import NacosSettings
                nacos_settings = NacosSettings(
                    SERVER_ADDR=config.NACOS_SERVER_ADDR if config.NACOS_SERVER_ADDR else os.environ.get("NACOS_SERVER_ADDR"),
                    NAMESPACE=config.NACOS_NAMESPACE if config.NACOS_NAMESPACE else os.environ.get("NACOS_NAMESPACE"),
                    USERNAME=config.NACOS_USERNAME if config.NACOS_USERNAME else os.environ.get("NACOS_USERNAME"),
                    PASSWORD=config.NACOS_PASSWORD if config.NACOS_PASSWORD else os.environ.get("NACOS_PASSWORD"),
                    SERVICE_GROUP=config.NACOS_GROUP if config.NACOS_GROUP else os.environ.get("NACOS_GROUP", "DEFAULT_GROUP"),
                    SERVICE_PORT=config.APP_PORT,
                    SERVICE_NAME=config.APP_NAME,
                    APP_CONN_LABELS={"version": config.APP_VERSION} if config.APP_VERSION else None,
                    SERVICE_META_DATA={"transport": config.TRANSPORT_TYPE},
                )
                from nacos_mcp import NacosMCP
                mcp = NacosMCP(name=config.APP_NAME,
                               nacos_settings=nacos_settings,
                               instructions=config.APP_DESCRIPTION,
                               version=config.APP_VERSION,
                               auth_server_provider=None)
        log.info("fast mcp initialized successfully")
        return mcp

    async def run_mcp_server(self):
        from mcp_service import load_mcp_plugins
        load_mcp_plugins("mcp_service")
        if not self.mcp:
            log.warning("MCP is not initialized, skipping MCP server startup.")
            return
        if config.TRANSPORT_TYPE == "stdio":
            await self.mcp.run_stdio_async()
        elif config.TRANSPORT_TYPE == "sse":
            await self.mcp.run_sse_async()
        elif config.TRANSPORT_TYPE == "streamable-http":
            await self.mcp.run_streamable_http_async()
        else:
            log.error(f"Unsupported TRANSPORT_TYPE: {config.TRANSPORT_TYPE}")

    def mount_mcp_app(self,app):
        if config.TRANSPORT_TYPE == "stdio":
            self.mcp.run(transport=config.TRANSPORT_TYPE)
        elif config.TRANSPORT_TYPE == "sse":
            app.mount("/", app.mcp.sse_app(), name="mcp_see")
        elif config.TRANSPORT_TYPE == "streamable-http":
            app.mount("/", app.mcp.streamable_http_app(), name="mcp_streamable_http")