import asyncio
import sys


def test_retrieve_qa_kb_does_not_access_ctx_outside_request(monkeypatch):
    """Regression: background tasks must not touch request-scoped ctx.

    Key point: retrieve_qa_kb schedules a background task; that task must not read
    request-scoped ctx after the request is over.

    This repo wires `mcp_context` at runtime; for unit tests we stub it.
    """

    # Stub mcp_context.get() before importing qa_memory_tools (module-level decorator).
    import libs

    class DummyMCP:
        def tool(self, *args, **kwargs):
            def _decorator(fn):
                return fn

            return _decorator

    class DummyMCPCtx:
        @staticmethod
        def get():
            return DummyMCP()

    monkeypatch.setattr(libs, "mcp_context", DummyMCPCtx())

    # Make sure we import qa_memory_tools fresh (it may have been imported earlier).
    sys.modules.pop("mcp_service.qa_memory_tools", None)

    from mcp_service import qa_memory_tools

    class Ctx:
        def __init__(self):
            self._allowed = True

        @property
        def client_id(self):
            if not self._allowed:
                raise RuntimeError("ctx accessed after request")
            return "client-123"

    ctx = Ctx()

    async def fake_retrieve_qa_kb(**kwargs):
        return {
            "schema_version": 1,
            "results": [
                {
                    "qa_id": "qa-1",
                    "question": "q",
                    "answer": "a",
                }
            ],
            "meta": {},
        }

    async def fake_qa_record_hit(**kwargs):
        return {"ok": True}

    monkeypatch.setattr(qa_memory_tools.qaMemoryService, "retrieve_qa_kb", fake_retrieve_qa_kb)
    monkeypatch.setattr(qa_memory_tools.qaMemoryService, "qa_record_hit", fake_qa_record_hit)

    async def _run():
        resp = await qa_memory_tools.retrieve_qa_kb(ctx=ctx, query="hello", namespace="ns", top_k=1)
        assert resp["results"] and resp["results"][0]["qa_id"] == "qa-1"

        ctx._allowed = False
        await asyncio.sleep(0)

    asyncio.run(_run())
