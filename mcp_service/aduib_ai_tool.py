from libs import mcp_context
from rpc.client.rag_service import RagService

mcp= mcp_context.get()
rag_service = RagService()


@mcp.tool(name="Retrieve information from documents", description="Retrieve information from documents such as PDFs, Word documents, and text files.")
async def retrieval_from_paragraph(query: str) -> str:
    return await rag_service.retrieval_from_paragraph(query)


@mcp.tool(name="Retrieve information from Q&A pairs", description="Retrieve information from question and answer pairs.")
async def retrieval_from_qa(query: str) -> str:
    return await rag_service.retrieval_from_qa(query)


@mcp.tool(name="Retrieve information from browser history", description="Retrieve information from browser history within a optional time range. time format: YYYY-MM-DD HH:MM:SS")
async def retrieval_from_browser_history(query: str, start_time: str = None, end_time: str = None) -> str:
    return await rag_service.retrieval_from_browser_history(query, start_time, end_time)