from aduib_rpc.server.rpc_execution.service_call import client

@client(service_name="aduib-ai")
class RagService:
    """RAG Service for handling retrieval-augmented generation requests."""
    async def retrieval_from_paragraph(self, query: str) -> str:
        ...

    async def retrieval_from_qa(self, query: str) -> str:
        ...

    async def retrieval_from_browser_history(self, query: str,start_time: str = None,end_time: str = None) -> str:
        ...
