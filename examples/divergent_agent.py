from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk" / "python"))

from agentlens import AgentLensClient


client = AgentLensClient()


def emit_run(*, recalled_memory: str, tool_condition: str, final_answer: str) -> str:
    run_id = client.new_run()
    client.emit(type="run.start", run_id=run_id, payload={"task": "decide whether to jog tomorrow morning"})

    client.emit(
        type="memory.recall",
        run_id=run_id,
        payload={
            "content": recalled_memory,
            "reason": "retrieved from recent user preference memory",
        },
    )

    llm_req = client.emit(
        type="llm.request",
        run_id=run_id,
        payload={
            "model": "gpt-4o-mini",
            "prompt": "Should we trust the recalled memory or confirm using weather tool?",
        },
    )

    client.emit(
        type="llm.response",
        run_id=run_id,
        parent_span_id=llm_req.span_id,
        payload={
            "decision": "call_weather_tool",
            "reason": "Need a fresh weather signal before final answer",
        },
        metrics={"latency_ms": 45, "input_tokens": 31, "output_tokens": 18},
    )

    tool_call = client.emit(
        type="tool.call",
        run_id=run_id,
        payload={"tool_name": "weather.get_forecast", "args": {"city": "Shanghai", "time": "tomorrow 7am"}},
    )

    client.emit(
        type="tool.result",
        run_id=run_id,
        parent_span_id=tool_call.span_id,
        payload={"condition": tool_condition, "temperature_c": 18},
        metrics={"latency_ms": 28},
    )

    if "sunny" in recalled_memory.lower() and tool_condition == "rain":
        client.emit(
            type="error",
            run_id=run_id,
            payload={
                "message": "Recalled memory conflicts with fresh weather tool result",
                "kind": "memory_conflict",
            },
            status="error",
        )

    client.emit(
        type="run.end",
        run_id=run_id,
        payload={"final_answer": final_answer},
    )
    return run_id


run_a = emit_run(
    recalled_memory="User usually jogs when the forecast is sunny.",
    tool_condition="sunny",
    final_answer="Jog is fine tomorrow morning.",
)
run_b = emit_run(
    recalled_memory="User usually jogs when the forecast is sunny.",
    tool_condition="rain",
    final_answer="Jog is fine tomorrow morning.",
)

print(f"Generated divergent runs: {run_a} and {run_b}")
