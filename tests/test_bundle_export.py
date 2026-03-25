from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from bundle_export import build_bundle_manifest, export_bundle

ROOT = Path(__file__).resolve().parents[1]


def test_build_bundle_manifest_contains_summary():
    trace_path = Path('demo.jsonl')
    events = [
        {'run_id': 'run-123', 'type': 'run.start', 'payload': {}},
        {'run_id': 'run-123', 'type': 'error', 'payload': {'kind': 'memory_conflict', 'message': 'bad recall'}},
        {'run_id': 'run-123', 'type': 'run.end', 'payload': {'final_answer': 'jog is fine'}},
    ]

    manifest = build_bundle_manifest(trace_path, events)
    assert manifest['trace_file'] == 'demo.jsonl'
    assert manifest['run_id'] == 'run-123'
    assert manifest['summary']['failure_mode'] == 'memory_vs_tool_conflict'


def test_export_bundle_writes_zip_with_expected_files(tmp_path: Path):
    work = tmp_path / 'proj'
    traces_dir = work / '.agentlens' / 'traces'
    traces_dir.mkdir(parents=True)
    trace_path = traces_dir / 'demo.jsonl'
    trace_path.write_text(
        '\n'.join([
            json.dumps({'run_id': 'run-zip', 'type': 'run.start', 'payload': {}}),
            json.dumps({'run_id': 'run-zip', 'type': 'run.end', 'payload': {'final_answer': 'ok'}}),
        ]) + '\n',
        encoding='utf-8',
    )

    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(work)
        out = export_bundle('latest', include_diff=False)
    finally:
        os.chdir(previous_cwd)

    assert out.exists()
    with ZipFile(out) as zf:
        names = set(zf.namelist())
        assert 'manifest.json' in names
        assert 'artifacts/latest_trace.html' in names
        assert 'traces/demo.jsonl' in names
        manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
        assert manifest['run_id'] == 'run-zip'


def test_cli_bundle_export_emits_zip(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'divergent'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    bundle = subprocess.run([sys.executable, 'cli.py', 'bundle', 'export'], cwd=work, capture_output=True, text=True)
    assert bundle.returncode == 0, bundle.stderr

    bundles = list((work / 'artifacts' / 'bundles').glob('*.zip'))
    assert bundles, 'expected at least one bundle zip'
    with ZipFile(bundles[0]) as zf:
        assert 'manifest.json' in zf.namelist()
        assert 'artifacts/latest_trace.html' in zf.namelist()
