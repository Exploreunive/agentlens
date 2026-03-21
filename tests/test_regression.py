from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from regression import build_regression_report, summarize_regression

ROOT = Path(__file__).resolve().parents[1]


def test_summarize_regression_detects_worsened_candidate():
    baseline = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'run.end', 'payload': {'final_answer': 'skip jogging'}},
    ]
    candidate = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'error', 'payload': {'kind': 'memory_conflict', 'message': 'bad recall'}},
        {'type': 'run.end', 'payload': {'final_answer': 'jog is fine'}},
    ]

    result = summarize_regression(baseline, candidate)
    assert result['regression_detected'] is True
    assert result['candidate_final_answer'] == 'jog is fine'
    assert result['candidate_suspicious_signals'][0]['type'] == 'memory_conflict'


def test_build_regression_report_contains_core_sections():
    report = build_regression_report(
        'good-weather-answer',
        'baseline.jsonl',
        'candidate.jsonl',
        {
            'regression_detected': True,
            'baseline_final_answer': 'skip jogging',
            'candidate_final_answer': 'jog is fine',
            'baseline_suspicious_signals': [],
            'candidate_suspicious_signals': [{'type': 'memory_conflict'}],
            'divergence': {'event_index': 1},
        },
    )
    assert 'AgentLens Regression Report' in report
    assert 'regression_detected' in report
    assert 'First divergence' in report


def test_openai_wrapper_demo_emits_trace(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    result = subprocess.run([sys.executable, 'examples/openai_wrapper_demo.py'], cwd=work, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    traces = list((work / '.agentlens' / 'traces').glob('*.jsonl'))
    assert traces
