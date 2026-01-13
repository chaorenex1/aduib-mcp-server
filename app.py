import asyncio
import logging
import signal

from app_factory import create_app, init_crawler_pool
from libs import app_context
from mcp_factory import get_mcp_factory

logger = logging.getLogger(__name__)

"""
Main entry point for the AduibAI application.
{
    "mcpServers": {
        "aduib_server":{
            "type": "streamableHttp",
            "url": "http://10.0.0.124:5002",
            "headers": {
                "Authorization": "Bearer YOUR_API_KEY"
            }
        }
    }
}
"""
app=None
if not app_context.get():
    app=create_app()


async def run_mcp_server(**kwargs):
    """Run the MCP server."""
    from component.crawl4ai.crawler_pool import close_all

    init_crawler_pool(app)
    app_context.set(app)
    await get_mcp_factory().mount_mcp_app(app)
    import uvicorn
    config = uvicorn.Config(app=app, host=app.config.APP_HOST, port=app.config.APP_PORT, **kwargs)
    server = uvicorn.Server(config)

    def handle_shutdown(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")

    try:
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
    except (ValueError, OSError):
        pass

    try:
        await server.serve()
    finally:
        logger.info("Cleaning up resources...")
        await close_all()
        logger.info("Shutdown complete")


if __name__ == '__main__':
    asyncio.run(run_mcp_server())
