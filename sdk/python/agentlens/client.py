from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from .models import AgentLensEvent


class AgentLensClient:
    def __init__(self, storage_dir: str = ".agentlens/traces"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def new_run(self) -> str:
        return str(uuid.uuid4())

    def emit(
        self,
        *,
        type: str,
        run_id: str,
        payload: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        status: str = "ok",
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> AgentLensEvent:
        event = AgentLensEvent(
            type=type,
            run_id=run_id,
            payload=payload or {},
            metrics=metrics or {},
            status=status,
            span_id=span_id or str(uuid.uuid4()),
            parent_span_id=parent_span_id,
        )
        self._append_event(event)
        return event

    @contextmanager
    def span(
        self,
        *,
        run_id: str,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> Iterator[AgentLensEvent]:
        span_event = self.emit(
            type='agent.decision',
            run_id=run_id,
            payload={
                'name': name,
                **(payload or {}),
            },
            metrics=metrics,
            parent_span_id=parent_span_id,
        )
        try:
            yield span_event
        except Exception as exc:
            self.emit(
                type='error',
                run_id=run_id,
                payload={
                    'kind': 'span_error',
                    'message': str(exc),
                    'span_name': name,
                },
                status='error',
                parent_span_id=span_event.span_id,
            )
            raise

    def record_llm_call(
        self,
        *,
        run_id: str,
        model: str,
        prompt: str,
        response: Optional[str] = None,
        decision: Optional[str] = None,
        reason: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, AgentLensEvent]:
        request = self.emit(
            type='llm.request',
            run_id=run_id,
            payload={
                'model': model,
                'prompt': prompt,
            },
            parent_span_id=parent_span_id,
        )
        response_payload = {
            key: value
            for key, value in {
                'response': response,
                'decision': decision,
                'reason': reason,
            }.items()
            if value is not None
        }
        response_event = self.emit(
            type='llm.response',
            run_id=run_id,
            payload=response_payload,
            metrics=metrics,
            parent_span_id=request.span_id,
        )
        return {'request': request, 'response': response_event}

    def record_tool_call(
        self,
        *,
        run_id: str,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, AgentLensEvent]:
        call = self.emit(
            type='tool.call',
            run_id=run_id,
            payload={
                'tool_name': tool_name,
                'args': args or {},
            },
            parent_span_id=parent_span_id,
        )
        result_event = self.emit(
            type='tool.result',
            run_id=run_id,
            payload=result or {},
            metrics=metrics,
            parent_span_id=call.span_id,
        )
        return {'call': call, 'result': result_event}

    def record_memory_recall(
        self,
        *,
        run_id: str,
        content: str,
        reason: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> AgentLensEvent:
        payload = {'content': content}
        if reason is not None:
            payload['reason'] = reason
        return self.emit(
            type='memory.recall',
            run_id=run_id,
            payload=payload,
            parent_span_id=parent_span_id,
        )

    def record_memory_write(
        self,
        *,
        run_id: str,
        content: str,
        memory_type: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> AgentLensEvent:
        payload = {'content': content}
        if memory_type is not None:
            payload['memory_type'] = memory_type
        return self.emit(
            type='memory.write',
            run_id=run_id,
            payload=payload,
            parent_span_id=parent_span_id,
        )

    def _append_event(self, event: AgentLensEvent) -> None:
        out = self.storage_dir / f"{event.run_id}.jsonl"
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
