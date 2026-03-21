from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sdk' / 'python'))

from agentlens import AgentLensClient
from agentlens.openai_wrapper import OpenAIResponsesTracer


client = AgentLensClient(redact_sensitive=True)
tracer = OpenAIResponsesTracer(client)
run_id = client.new_run()

client.emit(type='run.start', run_id=run_id, payload={'task': 'answer a simple weather planning question'})

with client.span(run_id=run_id, name='openai_wrapper_demo') as root_span:
    tracer.trace_chat_completion(
        run_id=run_id,
        model='gpt-4o-mini',
        prompt='Should I jog tomorrow morning in Shanghai if rain is likely? Contact me at test@example.com.',
        parent_span_id=root_span.span_id,
        call=lambda: {
            'output_text': 'You should probably skip jogging if rain is likely tomorrow morning.',
            'usage': {'input_tokens': 24, 'output_tokens': 16, 'total_tokens': 40},
            'finish_reason': 'stop',
        },
    )

client.emit(
    type='run.end',
    run_id=run_id,
    payload={'final_answer': 'You should probably skip jogging if rain is likely tomorrow morning.'},
)

print(f'Generated OpenAI wrapper demo run: {run_id}')
