from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk" / "python"))

from agentlens import AgentLensClient

client = AgentLensClient()


def emit_run(*, recalled_memory: str, tool_condition: str, final_answer: str, emit_conflict: bool) -> str:
    run_id = client.new_run()
    client.emit(type="run.start", run_id=run_id, payload={"task": "decide whether to jog tomorrow morning"})
    client.emit(type="memory.recall", run_id=run_id, payload={"content": recalled_memory, "reason": "retrieved from preference memory"})
    llm_req = client.emit(type="llm.request", run_id=run_id, payload={"model": "gpt-4o-mini", "prompt": "Decide whether to jog tomorrow based on memory and weather."})
    client.emit(type="llm.response", run_id=run_id, parent_span_id=llm_req.span_id, payload={"decision": "call_weather_tool", "reason": "Need fresh signal"}, metrics={"latency_ms": 44, "input_tokens": 29, "output_tokens": 15})
    tool_call = client.emit(type="tool.call", run_id=run_id, payload={"tool_name": "weather.get_forecast", "args": {"city": "Shanghai", "time": "tomorrow 7am"}})
    client.emit(type="tool.result", run_id=run_id, parent_span_id=tool_call.span_id, payload={"condition": tool_condition, "temperature_c": 17}, metrics={"latency_ms": 27})
    if emit_conflict:
        client.emit(type="error", run_id=run_id, payload={"message": "Stale recalled memory overrode fresh weather evidence", "kind": "stale_memory_override"}, status="error")
    client.emit(type="run.end", run_id=run_id, payload={"final_answer": final_answer})
    return run_id

run_good = emit_run(
    recalled_memory="User likes jogging when weather is sunny.",
    tool_condition="rain",
    final_answer="Better skip jogging tomorrow morning because rain is expected.",
    emit_conflict=False,
)
run_bad = emit_run(
    recalled_memory="User likes jogging when weather is sunny.",
    tool_condition="rain",
    final_answer="Jog is fine tomorrow morning.",
    emit_conflict=True,
)

print(f"Generated visible-failure runs: {run_good} and {run_bad}")
