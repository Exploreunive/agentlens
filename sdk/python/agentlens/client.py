from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

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

    def _append_event(self, event: AgentLensEvent) -> None:
        out = self.storage_dir / f"{event.run_id}.jsonl"
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
