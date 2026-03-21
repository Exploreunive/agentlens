from __future__ import annotations

import json
from pathlib import Path

from agentlens import AgentLensClient, redact_payload, redact_string


def test_emit_writes_jsonl(tmp_path: Path):
    storage = tmp_path / 'traces'
    client = AgentLensClient(str(storage))
    run_id = client.new_run()
    client.emit(type='run.start', run_id=run_id, payload={'task': 'hello'})

    files = list(storage.glob('*.jsonl'))
    assert len(files) == 1

    lines = files[0].read_text(encoding='utf-8').strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj['type'] == 'run.start'
    assert obj['run_id'] == run_id
    assert obj['payload']['task'] == 'hello'


def test_helper_methods_and_span_emit_structured_events(tmp_path: Path):
    storage = tmp_path / 'traces'
    client = AgentLensClient(str(storage))
    run_id = client.new_run()

    with client.span(run_id=run_id, name='root_flow', payload={'phase': 'test'}) as span_event:
        llm_events = client.record_llm_call(
            run_id=run_id,
            model='gpt-4o-mini',
            prompt='hello',
            response='hi',
            decision='reply',
            reason='simple greeting',
            metrics={'latency_ms': 12, 'input_tokens': 3, 'output_tokens': 2},
            parent_span_id=span_event.span_id,
        )
        client.record_tool_call(
            run_id=run_id,
            tool_name='weather.get_forecast',
            args={'city': 'Shanghai'},
            result={'condition': 'sunny'},
            metrics={'latency_ms': 8},
            parent_span_id=llm_events['response'].span_id,
        )
        client.record_memory_recall(
            run_id=run_id,
            content='User likes jogging in sunny weather',
            reason='recent preference memory',
            parent_span_id=span_event.span_id,
        )
        client.record_memory_write(
            run_id=run_id,
            content='Forecast was sunny',
            memory_type='episodic',
            parent_span_id=span_event.span_id,
        )

    records = [json.loads(line) for line in next(storage.glob('*.jsonl')).read_text(encoding='utf-8').splitlines() if line.strip()]
    types = [record['type'] for record in records]
    assert 'agent.decision' in types
    assert 'llm.request' in types
    assert 'llm.response' in types
    assert 'tool.call' in types
    assert 'tool.result' in types
    assert 'memory.recall' in types
    assert 'memory.write' in types


def test_redaction_helpers_mask_common_sensitive_values(tmp_path: Path):
    storage = tmp_path / 'traces'
    client = AgentLensClient(str(storage), redact_sensitive=True)
    run_id = client.new_run()
    client.emit(
        type='llm.request',
        run_id=run_id,
        payload={
            'prompt': 'Email me at test@example.com and use token ghp_secretToken12345',
            'api_key': 'sk-secret-value',
            'phone': '13800138000',
        },
    )

    record = json.loads(next(storage.glob('*.jsonl')).read_text(encoding='utf-8').strip())
    assert record['payload']['prompt'].count('[redacted_') >= 2
    assert record['payload']['api_key'] == '[redacted]'
    assert record['payload']['phone'] == '[redacted_phone]'

    assert redact_string('contact test@example.com') == 'contact [redacted_email]'
    assert redact_payload({'token': 'ghp_abc12345678'})['token'] == '[redacted_secret]'
