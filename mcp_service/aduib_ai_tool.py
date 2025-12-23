from libs import mcp_context
from rpc.client.rag_service import RagService

mcp= mcp_context.get()
rag_service = RagService()


@mcp.tool(name="Retrieve information from Doc Knowledge Base", description="Retrieve information from knowledge base documents.")
async def retrieval_from_paragraph(query: str) -> str:
    return await rag_service.retrieval_from_paragraph(query)


@mcp.tool(name="Retrieve information from QA Knowledge Base", description="Retrieve information from knowledge base QA pairs.")
async def retrieval_from_qa(query: str) -> str:
    return await rag_service.retrieval_from_qa(query)


@mcp.tool(name="Retrieve information from My Browser History", description="Retrieve information from user's browser history within a specified time range.")
async def retrieval_from_browser_history(query: str, start_time: str = None, end_time: str = None) -> str:
    return await rag_service.retrieval_from_browser_history(query, start_time, end_time)