from __future__ import annotations

from pathlib import Path
from typing import Optional

from bundle_export import export_bundle

CASEFILES_DIR = Path('artifacts/cases')


def case_dir_path(trace_name: str) -> Path:
    return CASEFILES_DIR / Path(trace_name).stem


def write_case_index(
    *,
    trace_name: str,
    trace_view_path: str,
    final_answer: str | None,
    priority_level: str,
    priority_score: int,
    baseline_name: Optional[str] = None,
    regression_report_path: Optional[str] = None,
) -> Path:
    case_dir = case_dir_path(trace_name)
    case_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = export_bundle(trace_name, include_diff=True)
    lines = [
        '# AgentLens Case File',
        '',
        f'- trace: `{trace_name}`',
        f'- priority: `{priority_level}` ({priority_score}/100)',
        f'- final_answer: {final_answer}',
        f'- trace_view: `{trace_view_path}`',
        f'- bundle: `{bundle_path}`',
    ]
    if baseline_name:
        lines.append(f'- baseline_watch: `{baseline_name}`')
    if regression_report_path:
        lines.append(f'- regression_report: `{regression_report_path}`')

    lines += [
        '',
        '## Share Checklist',
        '- Open the trace view first.',
        '- Read the regression report if baseline watch is enabled.',
        '- Share the bundle zip when someone else needs the full artifact set.',
        '',
    ]

    out = case_dir / 'README.md'
    out.write_text('\n'.join(lines), encoding='utf-8')
    return out
