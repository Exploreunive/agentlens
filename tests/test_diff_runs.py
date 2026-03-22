from __future__ import annotations

from diff_runs import build_report, summarize
from analyzer import summarize_divergence


def test_build_report_includes_divergence_timeline_and_severity():
    a = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.result', 'payload': {'condition': 'rain'}},
        {'type': 'run.end', 'payload': {'final_answer': 'skip jogging'}},
    ]
    b = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.result', 'payload': {'condition': 'sunny'}},
        {'type': 'run.end', 'payload': {'final_answer': 'jog is fine'}},
    ]
    report = build_report('a.jsonl', 'b.jsonl', summarize(a), summarize(b), summarize_divergence(a, b))
    assert '## Divergence timeline' in report
    assert '- severity: `high`' in report
    assert 'payload_mismatch' in report
    assert 'A answer risk:' in report
    assert 'B answer risk:' in report
