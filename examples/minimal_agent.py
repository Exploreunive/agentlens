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

with client.span(run_id=run_id, name='decide_jogging_plan', payload={'step': 'collect_signal'}) as planning_span:
    llm_events = client.record_llm_call(
        run_id=run_id,
        model='gpt-4o-mini',
        prompt='User asks if they should jog tomorrow morning. Decide whether to call weather tool.',
        decision='call_weather_tool',
        reason='Need forecast before making recommendation',
        metrics={'latency_ms': 50, 'input_tokens': 28, 'output_tokens': 14},
        parent_span_id=planning_span.span_id,
    )

    time.sleep(0.03)
    weather = {'condition': random.choice(['rain', 'cloudy', 'sunny']), 'temperature_c': 18}
    client.record_tool_call(
        run_id=run_id,
        tool_name='weather.get_forecast',
        args={'city': 'Shanghai', 'time': 'tomorrow 7am'},
        result=weather,
        metrics={'latency_ms': 30},
        parent_span_id=llm_events['response'].span_id,
    )

    client.record_memory_write(
        run_id=run_id,
        memory_type='episodic',
        content=f"User asked jogging advice; forecast={weather['condition']}",
        parent_span_id=planning_span.span_id,
    )

answer = 'Jog is fine.' if weather['condition'] in {'sunny', 'cloudy'} else 'Better skip jogging due to rain.'
client.emit(
    type='run.end',
    run_id=run_id,
    payload={'final_answer': answer},
)

print(f"AgentLens trace written for run_id={run_id}")
