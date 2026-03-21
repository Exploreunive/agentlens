from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl')


def _normalize_dynamic_text(text: str) -> str:
    return UUID_RE.sub('<trace>.jsonl', text)


def test_latest_diff_matches_golden_snapshot(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    subprocess.run([sys.executable, 'cli.py', 'demo', 'divergent'], cwd=work, check=True)
    subprocess.run([sys.executable, 'cli.py', 'diff'], cwd=work, check=True)

    actual = (work / 'artifacts' / 'latest_diff.md').read_text(encoding='utf-8')
    golden = (ROOT / 'tests' / 'goldens' / 'latest_diff.md').read_text(encoding='utf-8')
    assert _normalize_dynamic_text(actual) == _normalize_dynamic_text(golden)


def test_regression_report_matches_golden_snapshot(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    subprocess.run([sys.executable, 'cli.py', 'demo', 'minimal'], cwd=work, check=True)
    subprocess.run([sys.executable, 'cli.py', 'baseline', 'save', 'golden-run'], cwd=work, check=True)
    subprocess.run([sys.executable, 'cli.py', 'demo', 'failure'], cwd=work, check=True)
    subprocess.run([sys.executable, 'cli.py', 'regression', 'check', 'golden-run'], cwd=work, check=True)

    actual = (work / 'artifacts' / 'regression_golden-run.md').read_text(encoding='utf-8')
    golden = (ROOT / 'tests' / 'goldens' / 'regression_golden-run.md').read_text(encoding='utf-8')
    assert _normalize_dynamic_text(actual) == _normalize_dynamic_text(golden)
