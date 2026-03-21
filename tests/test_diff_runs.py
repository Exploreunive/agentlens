from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_diff_runs_generates_report(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    subprocess.run([sys.executable, 'cli.py', 'demo'], cwd=work, check=True)
    subprocess.run([sys.executable, 'cli.py', 'demo'], cwd=work, check=True)
    diff = subprocess.run([sys.executable, 'diff_runs.py'], cwd=work, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stderr

    report = work / 'artifacts' / 'latest_diff.md'
    assert report.exists()
    text = report.read_text(encoding='utf-8')
    assert 'AgentLens Run Divergence' in text
    assert 'First divergence' in text
    assert 'Final answer' in text
