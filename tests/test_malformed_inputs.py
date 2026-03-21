from __future__ import annotations

import json
from pathlib import Path

import pytest

from regression import load_trace, save_baseline, load_baseline
from viewer import build_html
from agentlens.openai_wrapper import OpenAIResponsesTracer
from agentlens import AgentLensClient


def test_load_trace_handles_empty_file(tmp_path: Path):
    empty = tmp_path / 'empty.jsonl'
    empty.write_text('', encoding='utf-8')
    assert load_trace(empty) == []


def test_load_trace_raises_on_invalid_json(tmp_path: Path):
    broken = tmp_path / 'broken.jsonl'
    broken.write_text('{not-json}\n', encoding='utf-8')
    with pytest.raises(json.JSONDecodeError):
        load_trace(broken)


def test_build_html_handles_missing_optional_fields():
    html = build_html([
        {'type': 'run.start', 'run_id': 'run-1'},
        {'type': 'run.end', 'run_id': 'run-1'},
    ])
    assert 'AgentLens Trace Viewer' in html
    assert 'run-1' in html


def test_openai_wrapper_handles_missing_usage_and_output(tmp_path: Path):
    storage = tmp_path / 'traces'
    client = AgentLensClient(str(storage))
    tracer = OpenAIResponsesTracer(client)
    run_id = client.new_run()

    response = tracer.trace_chat_completion(
        run_id=run_id,
        model='gpt-4o-mini',
        prompt='hello',
        call=lambda: {'finish_reason': 'stop'},
    )

    assert response['finish_reason'] == 'stop'
    records = [json.loads(line) for line in next(storage.glob('*.jsonl')).read_text(encoding='utf-8').splitlines() if line.strip()]
    assert records[-1]['payload']['finish_reason'] == 'stop'
    assert records[-1]['metrics']['total_tokens'] == 0


def test_load_baseline_raises_for_missing_saved_file(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_baseline('missing-baseline')
    finally:
        os.chdir(previous_cwd)


def test_save_baseline_and_load_baseline_with_missing_trace_file(tmp_path: Path):
    work = tmp_path / 'proj'
    traces_dir = work / '.agentlens' / 'traces'
    traces_dir.mkdir(parents=True)
    trace_file = traces_dir / 'demo.jsonl'
    trace_file.write_text('{"type":"run.start","payload":{}}\n', encoding='utf-8')

    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(work)
        save_baseline('dangling', trace_file)
        trace_file.unlink()
        with pytest.raises(FileNotFoundError):
            load_baseline('dangling')
    finally:
        os.chdir(previous_cwd)
