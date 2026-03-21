from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_viewer_contains_failure_summary_and_suspicious_signals(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    subprocess.run([sys.executable, 'examples/divergent_agent.py'], cwd=work, check=True)
    subprocess.run([sys.executable, 'viewer.py'], cwd=work, check=True)

    html_file = work / 'artifacts' / 'latest_trace.html'
    html = html_file.read_text(encoding='utf-8')
    assert 'failure summary' in html
    assert 'suspicious signals' in html
    assert 'memory_conflict' in html
    assert 'total latency' in html
    assert 'input tokens' in html
    assert 'tool calls' in html
    assert '<strong>event counts</strong>' in html
    assert 'first suspicious step' in html
    assert 'likely failure step' in html
    assert 'event filters' in html
    assert 'data-event-filter="error"' in html
    assert 'Event #6' in html
