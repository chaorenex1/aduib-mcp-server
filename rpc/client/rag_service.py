from typing import Any

from aduib_rpc.server.rpc_execution.service_call import client


@client(service_name="aduib-ai")
class RagService:
    """RAG Service for handling retrieval-augmented generation requests."""
    async def retrieval_from_paragraph(self, query: str) -> dict[str, Any]:
        ...

    async def retrieval_from_qa(self, query: str) -> dict[str, Any]:
        ...

    async def retrieval_from_browser_history(self, query: str,start_time: str = None,end_time: str = None) -> dict[str, Any]:
        ...

    async def retrieve_With_doc_id(self, doc_id: int) -> dict[str, Any]:
        """
        Retrieve a single document by its database identifier.

        Args:
            doc_id: Primary key of the knowledge document.
        """
        ...
