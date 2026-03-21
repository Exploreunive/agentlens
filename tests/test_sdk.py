from __future__ import annotations

import json
from pathlib import Path

from agentlens import AgentLensClient


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
