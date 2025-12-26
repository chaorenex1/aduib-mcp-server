import asyncio

from app_factory import create_app, init_crawler_pool
from libs import app_context
from mcp_factory import get_mcp_factory

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
    init_crawler_pool(app)
    app_context.set(app)
    await get_mcp_factory().mount_mcp_app(app)
    import uvicorn
    config = uvicorn.Config(app=app, host=app.config.APP_HOST, port=app.config.APP_PORT, **kwargs)
    await uvicorn.Server(config).serve()


if __name__ == '__main__':
    asyncio.run(run_mcp_server())