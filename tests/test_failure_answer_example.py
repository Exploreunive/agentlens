from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_failure_answer_example_emits_two_runs(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)
    result = subprocess.run([sys.executable, 'examples/failure_answer_agent.py'], cwd=work, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    traces = list((work / '.agentlens' / 'traces').glob('*.jsonl'))
    assert len(traces) >= 2
