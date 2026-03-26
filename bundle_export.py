from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from analyzer import summarize_divergence, summarize_run
from diff_runs import build_report as build_diff_report
from diff_runs import summarize as summarize_trace
from regression import list_traces, load_trace, resolve_trace_path
from viewer import build_html

TRACE_DIR = Path('.agentlens/traces')
OUT_DIR = Path('artifacts/bundles')
SAFE_NAME_RE = re.compile(r'[^A-Za-z0-9._-]+')


def _safe_slug(value: str) -> str:
    cleaned = SAFE_NAME_RE.sub('-', value.strip())
    return cleaned.strip('-') or 'trace'
def build_bundle_manifest(trace_path: Path, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = summarize_run(events)
    return {
        'bundle_version': '0.1',
        'trace_file': trace_path.name,
        'run_id': events[0].get('run_id') if events else None,
        'event_count': len(events),
        'summary': {
            'final_answer': summary.get('final_answer'),
            'failure_mode': summary.get('failure_mode'),
            'answer_risk': summary.get('answer_risk'),
            'confidence': summary.get('confidence'),
            'suspicious_signals': summary.get('suspicious_signals', []),
        },
    }


def build_bundle(trace_path: Path, *, include_diff: bool = True) -> Dict[str, Any]:
    events = load_trace(trace_path)
    manifest = build_bundle_manifest(trace_path, events)
    html = build_html(events)

    diff_markdown = None
    diff_source = None
    if include_diff:
        traces = list_traces()
        if len(traces) >= 2:
            other = next((path for path in traces if path != trace_path), None)
            if other is not None:
                other_events = load_trace(other)
                diff_markdown = build_diff_report(
                    other.name,
                    trace_path.name,
                    summarize_trace(other_events),
                    summarize_trace(events),
                    summarize_divergence(other_events, events),
                )
                diff_source = other.name

    return {
        'manifest': manifest,
        'trace_jsonl': '\n'.join(json.dumps(event, ensure_ascii=False) for event in events) + ('\n' if events else ''),
        'html': html,
        'diff_markdown': diff_markdown,
        'diff_source': diff_source,
    }


def export_bundle(trace_name: Optional[str] = None, *, include_diff: bool = True) -> Path:
    trace_path = resolve_trace_path(trace_name)
    bundle = build_bundle(trace_path, include_diff=include_diff)

    run_id = bundle['manifest'].get('run_id') or trace_path.stem
    out_name = f"{_safe_slug(run_id)}.zip"
    out_path = OUT_DIR / out_name
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with ZipFile(out_path, 'w', compression=ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(bundle['manifest'], ensure_ascii=False, indent=2) + '\n')
        zf.writestr(f"traces/{trace_path.name}", bundle['trace_jsonl'])
        zf.writestr('artifacts/latest_trace.html', bundle['html'])
        if bundle['diff_markdown'] is not None:
            zf.writestr('artifacts/latest_diff.md', bundle['diff_markdown'])

    return out_path.resolve()
