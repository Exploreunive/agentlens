from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sdk' / 'python'))

from agentlens import AgentLensClient
from agentlens.openai_wrapper import OpenAIResponsesTracer


client = AgentLensClient(redact_sensitive=True)
tracer = OpenAIResponsesTracer(client)
run_id = client.new_run()


def run_openai_call(parent_span_id: str):
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise SystemExit('OPENAI_API_KEY is set, but the openai package is not installed. Run `pip install ".[openai]"`.') from exc

        client_kwargs = {'api_key': api_key}
        base_url = os.getenv('OPENAI_BASE_URL')
        if base_url:
            client_kwargs['base_url'] = base_url

        sdk_client = OpenAI(**client_kwargs)
        model = os.getenv('AGENTLENS_OPENAI_MODEL', 'gpt-4.1-mini')
        api_style = os.getenv('AGENTLENS_OPENAI_API_STYLE', 'responses').lower()
        prompt = 'Should I jog tomorrow morning in Shanghai if rain is likely? Keep it brief.'

        if api_style == 'chat':
            return tracer.trace_chat_completions_create(
                run_id=run_id,
                client=sdk_client,
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                parent_span_id=parent_span_id,
            )

        return tracer.trace_responses_create(
            run_id=run_id,
            client=sdk_client,
            model=model,
            input=prompt,
            parent_span_id=parent_span_id,
        )

    return tracer.trace_chat_completion(
        run_id=run_id,
        model='gpt-4o-mini',
        prompt='Should I jog tomorrow morning in Shanghai if rain is likely? Contact me at test@example.com.',
        parent_span_id=parent_span_id,
        call=lambda: {
            'output_text': 'You should probably skip jogging if rain is likely tomorrow morning.',
            'usage': {'input_tokens': 24, 'output_tokens': 16, 'total_tokens': 40},
            'finish_reason': 'stop',
        },
    )


def extract_final_answer(response):
    if hasattr(response, 'output_text') and getattr(response, 'output_text'):
        return getattr(response, 'output_text')
    if isinstance(response, dict):
        return response.get('output_text') or response.get('response')
    return 'OpenAI wrapper demo completed.'

client.emit(type='run.start', run_id=run_id, payload={'task': 'answer a simple weather planning question'})

with client.span(run_id=run_id, name='openai_wrapper_demo') as root_span:
    response = run_openai_call(root_span.span_id)

client.emit(
    type='run.end',
    run_id=run_id,
    payload={'final_answer': extract_final_answer(response)},
)

print(f'Generated OpenAI wrapper demo run: {run_id}')
