import asyncio
from multiprocessing.spawn import freeze_support

from app_factory import create_app, app_context, init_fast_mcp, run_mcp_server

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

async def run_app(**kwargs):
    init_fast_mcp(app)
    import uvicorn
    config = uvicorn.Config(app=app, host=app.config.APP_HOST, port=app.config.APP_PORT, **kwargs)
    run_mcp_server(app)
    await uvicorn.Server(config).serve()


if __name__ == '__main__':
    freeze_support()
    asyncio.run(run_app())