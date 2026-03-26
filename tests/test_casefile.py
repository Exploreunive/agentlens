from __future__ import annotations

import json
from pathlib import Path

from casefile import write_case_index


def test_write_case_index_creates_shareable_readme(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        (traces / 'demo.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'run-123', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'run-123', 'type': 'run.end', 'payload': {'final_answer': 'ok'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        out = write_case_index(
            trace_name='demo.jsonl',
            trace_view_path='artifacts/views/demo.html',
            final_answer='ok',
            priority_level='high',
            priority_score=90,
            baseline_name='golden',
            regression_report_path='artifacts/regressions/golden__demo.md',
        )
    finally:
        os.chdir(previous_cwd)

    assert out == Path('artifacts/cases/demo/README.md')
    text = (tmp_path / out).read_text(encoding='utf-8')
    assert 'AgentLens Case File' in text
    assert 'artifacts/views/demo.html' in text
    assert 'artifacts/regressions/golden__demo.md' in text
