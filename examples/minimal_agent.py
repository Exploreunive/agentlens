from __future__ import annotations

import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk" / "python"))

from agentlens import AgentLensClient


client = AgentLensClient()
run_id = client.new_run()

client.emit(type="run.start", run_id=run_id, payload={"task": "find weather and decide whether to jog"})

llm_req = client.emit(
    type="llm.request",
    run_id=run_id,
    payload={
        "model": "gpt-4o-mini",
        "prompt": "User asks if they should jog tomorrow morning. Decide whether to call weather tool.",
    },
)

time.sleep(0.05)

client.emit(
    type="llm.response",
    run_id=run_id,
    parent_span_id=llm_req.span_id,
    payload={
        "decision": "call_weather_tool",
        "reason": "Need forecast before making recommendation",
    },
    metrics={"latency_ms": 50, "input_tokens": 28, "output_tokens": 14},
)

tool_call = client.emit(
    type="tool.call",
    run_id=run_id,
    payload={"tool_name": "weather.get_forecast", "args": {"city": "Shanghai", "time": "tomorrow 7am"}},
)

time.sleep(0.03)
weather = {"condition": random.choice(["rain", "cloudy", "sunny"]), "temperature_c": 18}
client.emit(
    type="tool.result",
    run_id=run_id,
    parent_span_id=tool_call.span_id,
    payload=weather,
    metrics={"latency_ms": 30},
)

client.emit(
    type="memory.write",
    run_id=run_id,
    payload={"memory_type": "episodic", "content": f"User asked jogging advice; forecast={weather['condition']}"},
)

answer = "Jog is fine." if weather["condition"] in {"sunny", "cloudy"} else "Better skip jogging due to rain."
client.emit(
    type="run.end",
    run_id=run_id,
    payload={"final_answer": answer},
)

print(f"AgentLens trace written for run_id={run_id}")
