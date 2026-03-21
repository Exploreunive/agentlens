from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from analyzer import summarize_divergence, summarize_run

TRACE_DIR = Path('.agentlens/traces')
BASELINE_DIR = Path('.agentlens/baselines')


def load_trace(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def list_traces() -> List[Path]:
    return sorted(TRACE_DIR.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)


def save_baseline(name: str, trace_path: Path) -> Path:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_file = BASELINE_DIR / f'{name}.json'
    baseline_file.write_text(
        json.dumps({'name': name, 'trace_file': trace_path.name}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return baseline_file


def load_baseline(name: str) -> Tuple[Path, List[Dict[str, Any]]]:
    baseline_file = BASELINE_DIR / f'{name}.json'
    data = json.loads(baseline_file.read_text(encoding='utf-8'))
    trace_file = TRACE_DIR / data['trace_file']
    return trace_file, load_trace(trace_file)


def summarize_regression(baseline_events: List[Dict[str, Any]], candidate_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    baseline_summary = summarize_run(baseline_events)
    candidate_summary = summarize_run(candidate_events)
    divergence = summarize_divergence(baseline_events, candidate_events)

    baseline_signals = len(baseline_summary.get('suspicious_signals', []))
    candidate_signals = len(candidate_summary.get('suspicious_signals', []))
    worsened = candidate_signals > baseline_signals or baseline_summary.get('final_answer') != candidate_summary.get('final_answer')

    return {
        'regression_detected': worsened,
        'baseline_final_answer': baseline_summary.get('final_answer'),
        'candidate_final_answer': candidate_summary.get('final_answer'),
        'baseline_suspicious_signals': baseline_summary.get('suspicious_signals', []),
        'candidate_suspicious_signals': candidate_summary.get('suspicious_signals', []),
        'divergence': divergence.get('first_divergence'),
    }


def build_regression_report(baseline_name: str, baseline_trace: str, candidate_trace: str, regression: Dict[str, Any]) -> str:
    lines = [
        '# AgentLens Regression Report',
        '',
        f'- baseline: `{baseline_name}` ({baseline_trace})',
        f'- candidate: `{candidate_trace}`',
        f"- regression_detected: `{regression.get('regression_detected')}`",
        '',
        '## Final answer comparison',
        f"- baseline: {regression.get('baseline_final_answer')}",
        f"- candidate: {regression.get('candidate_final_answer')}",
        '',
        '## Suspicious signals',
        f"- baseline: {regression.get('baseline_suspicious_signals')}",
        f"- candidate: {regression.get('candidate_suspicious_signals')}",
        '',
        '## First divergence',
        f"- {regression.get('divergence')}",
    ]
    return '\n'.join(lines) + '\n'
