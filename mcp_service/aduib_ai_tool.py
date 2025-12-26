from typing import Any

from mcp_factory import get_mcp
from rpc.client.rag_service import RagService

mcp = get_mcp()

rag_service = RagService()


@mcp.tool(name="Retrieve information from Doc Knowledge Base")
async def retrieval_from_paragraph(query: str) -> dict[str, Any]:
    """
    Use this tool to search the documentation knowledge base for relevant passages.
Provide a concise query and optional filters. Prefer returning short, high-signal excerpts
with clear provenance (doc_id/path/url and chunk_id). Do not fabricate citations; only cite
returned sources.
    """
    return await rag_service.retrieval_from_paragraph(query)


@mcp.tool(name="Retrieve information from QA Knowledge Base")
async def retrieval_from_qa(query: str) -> dict[str, Any]:
    """
    Search the QA knowledge base for validated Q&A pairs relevant to the query.
Return concise answers with clear provenance (qa_id, dataset, url, timestamps).
Prefer high-confidence and recently updated entries when scores are close.
Do not fabricate citations; only cite returned sources.
    """
    return await rag_service.retrieval_from_qa(query)


@mcp.tool(name="Retrieve information from My Browser History")
async def retrieval_from_browser_history(query: str, start_time: str = None, end_time: str = None) -> dict[str, Any]:
    """
    Search the user's local browser history for matching URLs/titles.
Use query/domain/time filters to narrow results. Return only what is found in history,
with clear provenance (browser, profile, db_path, row_id). Do not fabricate results.
This tool is privacy-sensitive: retrieve the minimum needed and avoid exposing unrelated URLs.
    """
    return await rag_service.retrieval_from_browser_history(query, start_time, end_time)


@mcp.resource(
    "resource://knowledge-document/{doc_id}",
    name="Knowledge document by ID",
    description="Fetch a single knowledge document's content from the Doc Knowledge Base.",
)
async def read_knowledge_document(doc_id: str) -> dict[str, Any]:
    """
    Resource endpoint that exposes the Doc Knowledge Base document content via doc_id.
    """
    try:
        numeric_doc_id = int(doc_id)
    except (TypeError, ValueError):
        return {"doc_id": doc_id, "error": "doc_id must be an integer"}

    doc = await rag_service.retrieve_With_doc_id(numeric_doc_id)
    if not doc:
        return {"doc_id": numeric_doc_id, "error": "Document not found"}

    return doc
