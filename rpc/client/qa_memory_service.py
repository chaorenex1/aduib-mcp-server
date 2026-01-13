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

from typing import Any, Dict, List, Optional

from aduib_rpc.server.rpc_execution.service_call import client


@client(service_name="aduib-ai-app")
class QaMemoryService:

    async def retrieve_qa_kb(
        self,
        query: str,
        namespace: str,
        top_k: int = 8,
        filters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        1) Call QA Memory Service /qa/search
        2) Format results with [QA_REF qa-xxxx] anchors
        3) Fire /qa/hit with shown=true for each returned qa_id (hook for recording)
        """
        ...


    async def qa_record_hit(
        self,
        qa_id: str,
        namespace: str,
        used: bool = True,
        shown: bool = True,
        client: Optional[dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Explicit hook for clients to record 'used' hits.

        Recommended usage:
          - Wrapper parses final model output, finds anchors [QA_REF qa-xxxx]
          - For each qa_id, call qa_record_hit(qa_id, namespace, used=true)
        """
        ...


    async def qa_upsert_candidate(
        self,
        question_raw: str,
        answer_raw: str,
        namespace: str,
        tags: Optional[List[str]] = None,
        scope: Optional[Dict[str, str]] = None,
        time_sensitivity: str = "medium",
        evidence_refs: Optional[List[str]] = None,
        client: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ...


    async def qa_validate_and_update(
        self,
        qa_id: str,
        namespace: str,
        result: str,
        signal_strength: str = "weak",
        reason: str = "",
        evidence_refs: Optional[List[str]] = None,
        execution: Optional[dict[str, Any]] = None,
        client: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Hook for execution-based validation.

        Typical flow on client side:
          - CLI runs command/tests produced from an answer that used QA_REF qa-xxxx
          - CLI collects exit_code, test result, log digests
          - CLI or wrapper calls this tool to inform QA Memory Service
        """
        ...
