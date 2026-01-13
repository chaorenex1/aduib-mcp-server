"""
MCP Wrapper for QA Memory Service

- Exposes MCP tools to Codex CLI / Claude Code (or any MCP client)
- Bridges tools to HTTP QA Memory Service (FastAPI)
- Implements hooks INSIDE tools:
  - retrieve_qa_kb: search + auto "shown" hit recording
  - qa_record_hit: explicit recording for "used" hits
  - qa_upsert_candidate: write candidate QA entries
  - qa_validate_and_update: apply execution validation signals
"""

import asyncio
from typing import Any, Dict, List, Optional

from mcp_factory import get_mcp

mcp = get_mcp()

from rpc.client.qa_memory_service import QaMemoryService
qaMemoryService = QaMemoryService()


# ---------- helpers for anchors and formatting ----------

def _make_anchor(qa_id: str) -> str:
    """Stable anchor format for referencing QA items."""
    return f"[QA_REF {qa_id}]"


def _format_result_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format one QA result item from QA Memory Service into a structure
    that is easy for MCP clients to consume.
    """
    qa_id = item["qa_id"]
    anchor = _make_anchor(qa_id)
    question = item.get("question") or ""
    answer = item.get("answer") or ""

    # A compact text representation that clients can inject into prompt.
    # Clients should preserve the anchor line verbatim to enable "used" tracking.
    render_lines = [
        f"{anchor}",
        f"Q: {question}",
        f"A: {answer}",
    ]
    render_text = "\n".join(render_lines)

    return {
        "qa_id": qa_id,
        "anchor": anchor,
        "question": question,
        "answer": answer,
        "validation_level": item.get("validation_level"),
        "confidence": item.get("confidence"),
        "scope": item.get("scope") or {},
        "tags": item.get("tags") or [],
        "source": item.get("source") or {},
        "expiry_at": item.get("expiry_at"),
        "relevance_score": item.get("relevance_score"),
        "evidence_refs": item.get("evidence_refs") or [],
        "resource_uri": item.get("resource_uri"),
        "render": render_text,
    }


# ---------- MCP tools ----------

@mcp.tool(
    name="retrieve_qa_kb",
    description=(
        "Search the QA memory base for relevant Q&A items. "
        "Returns items with QA_REF anchors to be injected into the prompt. "
        "This tool ALSO records 'shown' hits implicitly."
    ),
)
async def retrieve_qa_kb(
    query: str,
    namespace: str,
    top_k: int = 8,
) -> Dict[str, Any]:
    """
    1) Call QA Memory Service /qa/search
    2) Format results with [QA_REF qa-xxxx] anchors
    3) Fire /qa/hit with shown=true for each returned qa_id (hook for recording)
    """

    search_payload = {
        "query": query,
        "namespace": namespace,
        "top_k": top_k,
        "filters": None,  # you can extend filters via wrapper/tool schema if needed
    }

    search_resp = await qaMemoryService.retrieve_qa_kb(**search_payload)
    schema_version = search_resp.get("schema_version", 1)
    raw_results: List[Dict[str, Any]] = search_resp.get("results", [])

    formatted_results = [_format_result_item(r) for r in raw_results]

    # Snapshot request-bound context NOW; never touch ctx from background tasks.
    client_meta = {"client_id": "unknown"}

    # Hook: record "shown" hits asynchronously (do not block tool response)
    async def _record_shown_hits(client: Dict[str, Any], results: List[Dict[str, Any]]):
        if not results:
            return

        tasks = []
        for item in results:
            qa_id = item["qa_id"]
            hit_payload = {
                "qa_id": qa_id,
                "namespace": namespace,
                "shown": True,
                "used": False,
                "client": client,
            }
            tasks.append(qaMemoryService.qa_record_hit(**hit_payload))

        try:
            # fire-and-forget style; you may want to add logging / error handling
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            # best-effort background task; ignore cancellation during shutdown
            return

    # run the hook in background without delaying the main response
    if formatted_results:
        task = asyncio.create_task(_record_shown_hits(client_meta, formatted_results))
        # Ensure exceptions are consumed to avoid "Task exception was never retrieved".
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    return {
        "schema_version": schema_version,
        "results": formatted_results,
        "meta": search_resp.get("meta", {}),
    }


@mcp.tool(
    name="qa_record_hit",
    description=(
        "Record an explicit hit for a given QA entry. "
        "Use this tool when the model actually uses a QA item in its final answer "
        "(i.e., when a [QA_REF qa-xxxx] anchor is present in the output). "
        "This is the preferred way to report 'used=true' signals."
    ),
)
async def qa_record_hit(
    qa_id: str,
    namespace: str,
    used: bool = True,
    shown: bool = True,
) -> Dict[str, Any]:
    """
    Explicit hook for clients to record 'used' hits.

    Recommended usage:
      - Wrapper parses final model output, finds anchors [QA_REF qa-xxxx]
      - For each qa_id, call qa_record_hit(qa_id, namespace, used=true)
    """
    client_meta = {
        "client_id": "unknown",
    }
    payload = {
        "qa_id": qa_id,
        "namespace": namespace,
        "shown": shown,
        "used": used,
        "client": client_meta,
    }
    resp = await qaMemoryService.qa_record_hit(**payload)
    return resp


@mcp.tool(
    name="qa_upsert_candidate",
    description=(
        "Upsert a candidate QA entry into the QA memory (Level 1). "
        "Use this after generating a new solution that you want to store as a candidate, "
        "optionally after passing through a gatekeeper prompt."
    ),
)
async def qa_upsert_candidate(
    question_raw: str,
    answer_raw: str,
    namespace: str,
    tags: Optional[List[str]] = None,
    scope: Optional[Dict[str, str]] = None,
    time_sensitivity: str = "medium",
    evidence_refs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    client_meta = {
        "client_id": "unknown",
        "session_id": None,
        "user_id": None,
    }

    payload = {
        "question_raw": question_raw,
        "answer_raw": answer_raw,
        "tags": tags or [],
        "scope": scope or {},
        "time_sensitivity": time_sensitivity,
        "evidence_refs": evidence_refs or [],
        "namespace": namespace,
        "client": client_meta,
    }

    resp = await qaMemoryService.qa_upsert_candidate(**payload)
    return resp


@mcp.tool(
    name="qa_validate_and_update",
    description=(
        "Validate a QA entry based on execution results and update its state. "
        "Use this after running commands/tests that were derived from a QA-based answer. "
        "result: 'pass' | 'fail' | 'unknown'. "
        "signal_strength: 'strong' (tests/asserts) or 'weak' (only exit_code, no asserts)."
    ),
)
async def qa_validate_and_update(
    qa_id: str,
    namespace: str,
    result: str,
    signal_strength: str = "weak",
    reason: str = "",
    evidence_refs: Optional[List[str]] = None,
    exit_code: Optional[int] = None,
    stdout_digest: Optional[str] = None,
    stderr_digest: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Hook for execution-based validation.

    Typical flow on client side:
      - CLI runs command/tests produced from an answer that used QA_REF qa-xxxx
      - CLI collects exit_code, test result, log digests
      - CLI or wrapper calls this tool to inform QA Memory Service
    """
    client_meta = {
        "client_id": "unknown",
    }

    execution: Dict[str, Any] = {}
    if exit_code is not None:
        execution["exit_code"] = exit_code
    if stdout_digest is not None:
        execution["stdout_digest"] = stdout_digest
    if stderr_digest is not None:
        execution["stderr_digest"] = stderr_digest

    payload = {
        "qa_id": qa_id,
        "namespace": namespace,
        "result": result,
        "signal_strength": signal_strength,
        "reason": reason,
        "evidence_refs": evidence_refs or [],
        "execution": execution,
        "client": client_meta,
    }

    resp = await qaMemoryService.qa_validate_and_update(**payload)
    return resp
