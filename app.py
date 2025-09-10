import asyncio

from app_factory import create_app, init_crawler_pool
from libs import mcp_context, app_context

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
    from mcp_factory import MCPFactory
    import uvicorn

    mcp_factory = MCPFactory.get_mcp_factory()
    mcp = mcp_factory.get_mcp()
    mcp_context.set(mcp)
    app.mcp = mcp
    init_crawler_pool(app)
    app_context.set(app)
    await mcp_factory.mount_mcp_app(app)
    config = uvicorn.Config(app=app, host=app.config.APP_HOST, port=app.config.APP_PORT, **kwargs)
    await uvicorn.Server(config).serve()


if __name__ == '__main__':
    asyncio.run(run_mcp_server())