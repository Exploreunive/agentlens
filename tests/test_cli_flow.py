from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cli_demo_and_view(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    view = subprocess.run([sys.executable, 'cli.py', 'view'], cwd=work, capture_output=True, text=True)
    assert view.returncode == 0, view.stderr

    traces = list((work / '.agentlens' / 'traces').glob('*.jsonl'))
    assert traces, 'expected at least one trace file'

    html_file = work / 'artifacts' / 'latest_trace.html'
    assert html_file.exists()
    html = html_file.read_text(encoding='utf-8')
    assert 'AgentLens Trace Viewer' in html
