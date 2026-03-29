from __future__ import annotations

import html
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from benchmark_report import collect_benchmark_gate_status, resolve_benchmark_baseline_name
from bundle_export import export_bundle

CASEFILES_DIR = Path('artifacts/cases')
CASE_BOARD_OUT = CASEFILES_DIR / 'index.html'
DEFAULT_CASE_STATUS = 'new'
DEFAULT_CASE_OWNER = 'unassigned'
VALID_CASE_STATUSES = {'new', 'investigating', 'recurring', 'fixed', 'ignored'}


def _metadata_line(key: str, value: str | None) -> str:
    return f'- {key}: `{value}`'


def _extract_backtick_value(line: str, key: str) -> str | None:
    prefix = f'- {key}: `'
    if line.startswith(prefix) and line.endswith('`'):
        return line[len(prefix):-1]
    return None


def _suggest_next_step(
    *,
    regression_report_path: str | None,
    trace_view_path: str,
    failure_mode: str | None = None,
) -> str:
    if regression_report_path:
        return 'Compare the regression report with the trace view and identify the first changed decision.'
    if failure_mode and failure_mode != 'no_explicit_failure':
        return f'Open the trace view and confirm the first event that supports {failure_mode}.'
    return f'Open {trace_view_path} and verify whether the final answer is grounded in tool evidence.'


def _recheck_commands(
    *,
    trace_name: str,
    baseline_name: str | None,
    benchmark_baseline_name: str | None,
) -> list[str]:
    stem = Path(trace_name).stem
    commands = [
        f'python3 cli.py view {stem}',
        'python3 cli.py inbox' + (f' --baseline {baseline_name}' if baseline_name else ''),
    ]
    if baseline_name:
        commands.append(f'python3 cli.py regression check {baseline_name}')
    if benchmark_baseline_name:
        commands.append(f'python3 cli.py bench check {benchmark_baseline_name}')
    commands.append('pytest -q')
    return commands


def _repair_checklist_items(
    *,
    failure_mode: str | None,
    regression_detected: bool,
    benchmark_baseline_name: str | None,
) -> list[str]:
    items = ['Confirm the failure in the trace view.']
    if regression_detected:
        items.append('Compare the candidate run against the saved baseline and identify the first changed decision.')
    if failure_mode and failure_mode != 'no_explicit_failure':
        items.append(f'Write a targeted fix for {failure_mode} instead of broad heuristic changes.')
    else:
        items.append('Capture the first wrong decision or missing check before changing heuristics.')
    if benchmark_baseline_name:
        items.append(f'Re-run the benchmark gate against {benchmark_baseline_name}.')
    items.append('Re-run the incident workflow and mark the case fixed only after the recheck commands are clean.')
    return items


def _fix_validation_summary(
    *,
    case_status: str,
    regression_detected: bool,
    benchmark_gate: dict[str, Any] | None,
) -> dict[str, str | bool]:
    benchmark_regressions = int((benchmark_gate or {}).get('regressions', 0))
    baseline_ok = not regression_detected
    benchmark_ok = benchmark_regressions == 0
    if baseline_ok and benchmark_ok and case_status == 'fixed':
        status = 'verified'
        recommendation = 'Safe to keep this case fixed unless the fingerprint reappears.'
    elif baseline_ok and benchmark_ok:
        status = 'ready_to_close'
        recommendation = 'Validation is clean. You can mark this case fixed after a final review.'
    else:
        status = 'blocked'
        recommendation = 'Do not mark this case fixed yet. One or more validation gates are still failing.'
    return {
        'status': status,
        'baseline_ok': baseline_ok,
        'benchmark_ok': benchmark_ok,
        'recommendation': recommendation,
    }


def case_dir_path(trace_name: str) -> Path:
    return CASEFILES_DIR / Path(trace_name).stem


def parse_case_metadata(case_index_path: str | Path) -> dict[str, str]:
    path = Path(case_index_path)
    metadata = {
        'status': DEFAULT_CASE_STATUS,
        'owner': DEFAULT_CASE_OWNER,
        'next_step': '',
    }
    if not path.exists():
        return metadata
    for line in path.read_text(encoding='utf-8').splitlines():
        for key in ('status', 'owner', 'next_step'):
            value = _extract_backtick_value(line, key)
            if value is not None:
                metadata[key] = value
    return metadata


def parse_case_context(case_index_path: str | Path) -> dict[str, str | None]:
    path = Path(case_index_path)
    context = {
        'baseline_watch': None,
        'regression_report': None,
        'benchmark_baseline': None,
    }
    if not path.exists():
        return context
    for line in path.read_text(encoding='utf-8').splitlines():
        for key in ('baseline_watch', 'regression_report', 'benchmark_baseline'):
            value = _extract_backtick_value(line, key)
            if value is not None:
                context[key] = value
    return context


def write_case_index(
    *,
    trace_name: str,
    trace_view_path: str,
    final_answer: str | None,
    priority_level: str,
    priority_score: int,
    failure_mode: str | None = None,
    baseline_name: Optional[str] = None,
    regression_report_path: Optional[str] = None,
    status: str = DEFAULT_CASE_STATUS,
    owner: str | None = None,
    next_step: str | None = None,
) -> Path:
    case_dir = case_dir_path(trace_name)
    case_dir.mkdir(parents=True, exist_ok=True)
    out = case_dir / 'README.md'
    existing = parse_case_metadata(out)

    bundle_path = export_bundle(trace_name, include_diff=True)
    benchmark_baseline_name = resolve_benchmark_baseline_name()
    benchmark_gate = collect_benchmark_gate_status(benchmark_baseline_name)
    resolved_status = existing.get('status') or status
    if resolved_status not in VALID_CASE_STATUSES:
        resolved_status = DEFAULT_CASE_STATUS
    resolved_owner = existing.get('owner') or owner or DEFAULT_CASE_OWNER
    resolved_next_step = existing.get('next_step') or next_step or _suggest_next_step(
        regression_report_path=regression_report_path,
        trace_view_path=trace_view_path,
        failure_mode=failure_mode,
    )
    lines = [
        '# AgentLens Case File',
        '',
        f'- trace: `{trace_name}`',
        _metadata_line('status', resolved_status),
        _metadata_line('owner', resolved_owner),
        _metadata_line('next_step', resolved_next_step),
        f'- priority: `{priority_level}` ({priority_score}/100)',
        f'- final_answer: {final_answer}',
        f'- trace_view: `{trace_view_path}`',
        f'- bundle: `{bundle_path}`',
    ]
    if baseline_name:
        lines.append(f'- baseline_watch: `{baseline_name}`')
    if regression_report_path:
        lines.append(f'- regression_report: `{regression_report_path}`')
    if benchmark_baseline_name:
        lines.append(f'- benchmark_baseline: `{benchmark_baseline_name}`')

    repair_items = _repair_checklist_items(
        failure_mode=failure_mode,
        regression_detected=bool(regression_report_path),
        benchmark_baseline_name=benchmark_baseline_name,
    )
    recheck_commands = _recheck_commands(
        trace_name=trace_name,
        baseline_name=baseline_name,
        benchmark_baseline_name=benchmark_baseline_name,
    )
    validation = _fix_validation_summary(
        case_status=resolved_status,
        regression_detected=bool(regression_report_path),
        benchmark_gate=benchmark_gate,
    )

    lines += [
        '',
        '## Incident Workflow',
        '- Move status from `new` -> `investigating` when someone starts work.',
        '- Use the recorded `next_step` as the smallest concrete debugging step.',
        '- Mark `fixed` only after the benchmark gate and regression watch are clean.',
        '',
        '## Repair Checklist',
    ]
    lines.extend(f'- [ ] {item}' for item in repair_items)
    lines += [
        '',
        '## Recheck Commands',
    ]
    lines.extend(f'- `{command}`' for command in recheck_commands)
    lines += [
        '',
        '## Fix Validation Summary',
        f"- validation_status: `{validation['status']}`",
        f"- baseline_validation: `{'clean' if validation['baseline_ok'] else 'regressed'}`",
        f"- benchmark_validation: `{'clean' if validation['benchmark_ok'] else 'regressed'}`",
        f"- closure_recommendation: {validation['recommendation']}",
        '',
        '## Share Checklist',
        '- Open the trace view first.',
        '- Read the regression report if baseline watch is enabled.',
        '- Share the bundle zip when someone else needs the full artifact set.',
        '',
    ]

    out.write_text('\n'.join(lines), encoding='utf-8')
    return out


def parse_case_status(case_index_path: str | Path) -> str:
    return parse_case_metadata(case_index_path).get('status', DEFAULT_CASE_STATUS)


def update_case_index(
    trace_name: str,
    *,
    status: str | None = None,
    owner: str | None = None,
    next_step: str | None = None,
    force: bool = False,
) -> Path:
    out = case_dir_path(trace_name) / 'README.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    if status is not None and status not in VALID_CASE_STATUSES:
        raise SystemExit(f'Invalid case status: {status}')
    metadata = parse_case_metadata(out)
    context = parse_case_context(out)
    target_status = status or metadata.get('status') or DEFAULT_CASE_STATUS
    benchmark_gate = collect_benchmark_gate_status(str(context.get('benchmark_baseline')) if context.get('benchmark_baseline') else None)
    validation = _fix_validation_summary(
        case_status=target_status,
        regression_detected=bool(context.get('regression_report')),
        benchmark_gate=benchmark_gate,
    )
    if target_status == 'fixed' and validation.get('status') not in {'verified'} and not force:
        raise SystemExit(
            'Case is not ready to mark fixed yet. '
            f"validation_status={validation.get('status')} "
            f"baseline={'clean' if validation.get('baseline_ok') else 'regressed'} "
            f"benchmark={'clean' if validation.get('benchmark_ok') else 'regressed'}. "
            'Use --force only if you intentionally want to override the validation guard.'
        )
    current_lines = out.read_text(encoding='utf-8').splitlines() if out.exists() else ['# AgentLens Case File', '']
    replacements = {
        'status': target_status,
        'owner': owner or metadata.get('owner') or DEFAULT_CASE_OWNER,
        'next_step': next_step or metadata.get('next_step') or '',
    }
    updated_lines: list[str] = []
    replaced_keys: set[str] = set()
    for line in current_lines:
        replaced = False
        for key, value in replacements.items():
            if _extract_backtick_value(line, key) is not None:
                updated_lines.append(_metadata_line(key, value))
                replaced_keys.add(key)
                replaced = True
                break
        if not replaced:
            updated_lines.append(line)
    insert_at = 2 if len(updated_lines) >= 2 else len(updated_lines)
    missing_lines = [_metadata_line(key, value) for key, value in replacements.items() if key not in replaced_keys]
    if missing_lines:
        updated_lines[insert_at:insert_at] = missing_lines
    out.write_text('\n'.join(updated_lines).rstrip() + '\n', encoding='utf-8')
    return out


def build_case_board_html(items: list[dict[str, Any]], benchmark_gate: Optional[dict[str, Any]] = None) -> str:
    regressions = [item for item in items if item.get('regression_detected')]
    unresolved_items = [
        item for item in items if (item.get('case_status') or DEFAULT_CASE_STATUS) not in {'fixed', 'ignored'}
    ]
    unresolved_regressions = [
        item for item in unresolved_items if item.get('regression_detected')
    ]
    validation_rows = [
        _fix_validation_summary(
            case_status=str(item.get('case_status') or DEFAULT_CASE_STATUS),
            regression_detected=bool(item.get('regression_detected')),
            benchmark_gate=benchmark_gate,
        )
        for item in items
    ]
    ready_to_close_count = sum(1 for row in validation_rows if row.get('status') == 'ready_to_close')
    investigating_items = [
        item for item in items if (item.get('case_status') or DEFAULT_CASE_STATUS) == 'investigating'
    ]
    unassigned_high_priority = [
        item
        for item in unresolved_items
        if (item.get('case_owner') or DEFAULT_CASE_OWNER) == DEFAULT_CASE_OWNER and item.get('priority_level') == 'high'
    ]
    action_queue = sorted(
        unresolved_items,
        key=lambda item: (
            not bool(item.get('regression_detected')),
            -int(item.get('priority_score', 0)),
            int(item.get('trace_recency_rank', 999999)),
            str(item.get('trace_file')),
        ),
    )[:5]
    top_cases = sorted(items, key=lambda item: (-int(item.get('priority_score', 0)), str(item.get('trace_file'))))[:6]
    statuses = Counter((item.get('case_status') or DEFAULT_CASE_STATUS) for item in items)
    fingerprint_labels = [
        (item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure'
        for item in items
    ]
    fingerprints = Counter(fingerprint_labels)
    trace_lookup = {str(item.get('trace_file')): item for item in items}
    leaderboard_rows: list[dict[str, Any]] = []
    for label in sorted(fingerprints):
        matching = [
            item for item in items
            if ((item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure') == label
        ]
        unresolved = sum(1 for item in matching if (item.get('case_status') or DEFAULT_CASE_STATUS) not in {'fixed', 'ignored'})
        regression_count = sum(1 for item in matching if item.get('regression_detected'))
        avg_priority = round(sum(int(item.get('priority_score', 0)) for item in matching) / len(matching))
        trace_names = [str(item.get('trace_file')) for item in matching]
        first_seen = sorted(trace_names)[0] if trace_names else 'n/a'
        latest_seen = min(
            trace_names,
            key=lambda name: int(trace_lookup.get(name, {}).get('trace_recency_rank', 999999)),
            default='n/a',
        )
        leaderboard_rows.append(
            {
                'label': label,
                'count': len(matching),
                'regressions': regression_count,
                'unresolved': unresolved,
                'avg_priority': avg_priority,
                'first_seen': first_seen,
                'latest_seen': latest_seen,
            }
        )
    leaderboard_rows.sort(key=lambda row: (-row['count'], -row['regressions'], -row['unresolved'], -row['avg_priority'], row['label']))
    recent_items = sorted(items, key=lambda item: int(item.get('trace_recency_rank', 999999)))
    split = max(1, len(recent_items) // 2)
    recent_window = recent_items[:split]
    older_window = recent_items[split:]
    recent_counter = Counter(
        (item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure'
        for item in recent_window
    )
    older_counter = Counter(
        (item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure'
        for item in older_window
    )
    trend_rows: list[tuple[str, int, int, int, str]] = []
    for label in sorted(set(recent_counter) | set(older_counter)):
        recent_count = recent_counter.get(label, 0)
        older_count = older_counter.get(label, 0)
        delta = recent_count - older_count
        if delta > 0:
            direction = 'rising'
        elif delta < 0:
            direction = 'cooling'
        else:
            direction = 'steady'
        trend_rows.append((label, recent_count, older_count, delta, direction))
    trend_rows.sort(key=lambda row: (-row[3], -row[1], row[0]))
    escalating_labels = {
        label
        for label, recent_count, older_count, delta, _direction in trend_rows
        if recent_count >= 2 and delta >= 1
    }
    escalating_items = [
        item
        for item in unresolved_items
        if ((item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure') in escalating_labels
    ]
    leaderboard_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">Recurring Issue</div>
          <div class="mini-value">{html.escape(str(row["label"]))}</div>
          <div class="mini-meta">cases {row["count"]} · regressions {row["regressions"]} · unresolved {row["unresolved"]} · avg priority {row["avg_priority"]}</div>
          <div class="mini-meta">first seen {html.escape(str(row["first_seen"]))} · latest seen {html.escape(str(row["latest_seen"]))}</div>
        </div>
        '''
        for row in leaderboard_rows[:6]
    ) or '<div class="empty">No recurring issues yet.</div>'
    trend_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">{"Escalating" if label in escalating_labels else "Trend"}</div>
          <div class="mini-value">{html.escape(label)}</div>
          <div class="mini-meta">recent {recent_count} · older {older_count} · {direction}</div>
        </div>
        '''
        for label, recent_count, older_count, _delta, direction in trend_rows[:6]
    ) or '<div class="empty">No trend data yet.</div>'
    owner_rows = Counter((item.get('case_owner') or DEFAULT_CASE_OWNER) for item in items)
    owner_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">Owner Load</div>
          <div class="mini-value">{html.escape(str(owner))}</div>
          <div class="mini-meta">cases {count}</div>
        </div>
        '''
        for owner, count in sorted(owner_rows.items(), key=lambda row: (-row[1], row[0]))[:6]
    ) or '<div class="empty">No owners assigned yet.</div>'
    gate = benchmark_gate or {}
    coverage = gate.get('coverage') or {}
    regressed_fixtures = gate.get('regressed_fixtures') or []
    gate_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">Benchmark Regression</div>
          <div class="mini-value">{html.escape(str(item.get("fixture")))}</div>
          <div class="mini-meta">coverage {html.escape(str(item.get("coverage_before")))} -> {html.escape(str(item.get("coverage_after")))}</div>
        </div>
        '''
        for item in regressed_fixtures[:4]
    )
    if not gate_cards:
        gate_cards = '<div class="empty">No benchmark regressions currently detected.</div>'
    focus_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">{html.escape(str(view["label"]))}</div>
          <div class="mini-value">{view["count"]}</div>
          <div class="mini-meta">{html.escape(str(view["description"]))}</div>
        </div>
        '''
        for view in [
            {
                'label': 'Unresolved Regressions',
                'count': len(unresolved_regressions),
                'description': 'Runs still open and already worse than baseline.',
            },
            {
                'label': 'Investigating Now',
                'count': len(investigating_items),
                'description': 'Cases currently owned and in active debugging.',
            },
            {
                'label': 'Escalating Now',
                'count': len(escalating_items),
                'description': 'Open incidents whose recurring fingerprint is rising in recent runs.',
            },
            {
                'label': 'Ready To Close',
                'count': ready_to_close_count,
                'description': 'Cases whose baseline and benchmark validation are both clean.',
            },
            {
                'label': 'Unassigned High Priority',
                'count': len(unassigned_high_priority),
                'description': 'High-risk incidents with no explicit owner yet.',
            },
        ]
    )
    queue_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">Next Action</div>
          <div class="mini-value">{html.escape(str(item.get("trace_file")))}</div>
          <div class="mini-meta">status {html.escape(str(item.get("case_status") or DEFAULT_CASE_STATUS))} · priority {html.escape(str(item.get("priority_score", 0)))} · {'baseline regression' if item.get('regression_detected') else 'incident review'}</div>
          <div class="mini-meta">owner {html.escape(str(item.get("case_owner") or DEFAULT_CASE_OWNER))}</div>
          <div class="mini-meta">{html.escape(str(item.get("case_next_step") or "No next step recorded yet."))}</div>
          <div class="mini-meta">recheck {'baseline + benchmark' if item.get('regression_detected') else 'trace + inbox'}</div>
          <div class="mini-meta">trend {'escalating' if (((item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure') in escalating_labels) else 'stable'}</div>
          <div class="mini-meta">validation {html.escape(str(_fix_validation_summary(case_status=str(item.get("case_status") or DEFAULT_CASE_STATUS), regression_detected=bool(item.get("regression_detected")), benchmark_gate=benchmark_gate).get("status")))}</div>
        </div>
        '''
        for item in action_queue
    ) or '<div class="empty">No unresolved cases right now.</div>'

    case_cards = ''.join(
        f'''
        <section class="case-card level-{html.escape(str(item.get("priority_level", "low")))}">
          <div class="case-head">
            <div>
              <div class="eyebrow">{'Regression case' if item.get('regression_detected') else 'Incident case'}</div>
              <h2>{html.escape(str(item.get('trace_file')))}</h2>
            </div>
            <div class="score">{html.escape(str(item.get('priority_score', 0)))}</div>
          </div>
          <div class="meta">
            <span>failure: <strong>{html.escape(str(item.get('failure_mode') or 'unknown'))}</strong></span>
            <span>fingerprint: <strong>{html.escape(str(((item.get('failure_fingerprint') or {}).get('label')) or 'unknown'))}</strong></span>
            <span>risk: <strong>{html.escape(str(item.get('answer_risk') or 'unknown'))}</strong></span>
            <span>status: <strong>{html.escape(str(item.get('case_status') or DEFAULT_CASE_STATUS))}</strong></span>
            <span>owner: <strong>{html.escape(str(item.get('case_owner') or DEFAULT_CASE_OWNER))}</strong></span>
            <span>baseline: <strong>{html.escape('regressed' if item.get('regression_detected') else 'clean')}</strong></span>
            <span>trend: <strong>{html.escape('escalating' if (((item.get('failure_fingerprint') or {}).get('label') or item.get('failure_mode') or 'unknown_failure') in escalating_labels) else 'stable')}</strong></span>
            <span>validation: <strong>{html.escape(str(_fix_validation_summary(case_status=str(item.get('case_status') or DEFAULT_CASE_STATUS), regression_detected=bool(item.get('regression_detected')), benchmark_gate=benchmark_gate).get('status')))}</strong></span>
          </div>
          <div class="answer">{html.escape(str(item.get('final_answer') or 'No final answer captured.'))}</div>
          <div class="answer" style="margin-top: 12px;">next step: {html.escape(str(item.get('case_next_step') or 'No next step recorded yet.'))}</div>
          <ul>
            <li>Case file: <code>{html.escape(str(item.get('case_index_path') or ''))}</code></li>
            <li>Trace page: <code>{html.escape(str(item.get('trace_view_path') or ''))}</code></li>
            <li>Regression report: <code>{html.escape(str(item.get('regression_report_path') or 'n/a'))}</code></li>
          </ul>
        </section>
        '''
        for item in top_cases
    ) or '<div class="empty">No cases available.</div>'

    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Incident Board</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07101d;
      --panel: rgba(14, 24, 40, 0.92);
      --border: #22324f;
      --text: #edf3fb;
      --muted: #9fb0c8;
      --accent: #7cc4ff;
      --high: #ff8a65;
      --medium: #ffd166;
      --low: #6dd3a0;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #132440 0%, var(--bg) 60%); color: var(--text); }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px 64px; }}
    h1, h2, h3 {{ margin: 0; }}
    p {{ color: var(--muted); line-height: 1.6; }}
    .hero {{ display: grid; gap: 18px; margin-bottom: 26px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }}
    .stat, .section, .case-card, .mini-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; }}
    .stat {{ padding: 18px; }}
    .stat-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat-value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
    .layout {{ display: grid; grid-template-columns: 1.1fr 1.1fr 1.8fr; gap: 16px; }}
    .queue-layout {{ display: grid; grid-template-columns: 1fr; gap: 16px; margin: 0 0 16px; }}
    .focus-layout {{ display: grid; grid-template-columns: 1.4fr 1.6fr; gap: 16px; margin: 0 0 16px; }}
    .gate-layout {{ display: grid; grid-template-columns: 1.1fr 2.9fr; gap: 16px; margin-top: 16px; }}
    .section {{ padding: 18px; }}
    .mini-grid {{ display: grid; gap: 12px; }}
    .mini-card {{ padding: 14px; }}
    .mini-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .mini-value {{ margin-top: 8px; font-size: 18px; font-weight: 700; }}
    .mini-meta {{ margin-top: 6px; color: var(--muted); }}
    .case-stack {{ display: grid; gap: 14px; }}
    .case-card {{ padding: 18px; }}
    .case-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; }}
    .eyebrow {{ color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }}
    .score {{ min-width: 58px; height: 58px; border-radius: 16px; display: grid; place-items: center; font-size: 22px; font-weight: 800; background: #0d1728; border: 1px solid var(--border); }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 16px; margin: 14px 0; color: var(--muted); }}
    .answer {{ padding: 12px 14px; border-radius: 14px; background: #0c1524; border: 1px solid var(--border); line-height: 1.6; white-space: pre-wrap; }}
    ul {{ margin: 14px 0 0; padding-left: 18px; color: var(--muted); }}
    li {{ margin: 8px 0; }}
    code {{ color: var(--accent); font-family: ui-monospace, SFMono-Regular, monospace; }}
    .level-high .score {{ border-color: rgba(255, 138, 101, 0.55); }}
    .level-medium .score {{ border-color: rgba(255, 209, 102, 0.55); }}
    .level-low .score {{ border-color: rgba(109, 211, 160, 0.55); }}
    .empty {{ color: var(--muted); }}
    @media (max-width: 900px) {{
      .stats, .layout, .queue-layout, .focus-layout, .gate-layout {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1>AgentLens Incident Board</h1>
        <p>The board for repeated agent failures, regressions, and the next cases worth debugging.</p>
      </div>
      <div class="stats">
        <div class="stat"><div class="stat-label">Cases</div><div class="stat-value">{len(items)}</div></div>
        <div class="stat"><div class="stat-label">Regressions</div><div class="stat-value">{len(regressions)}</div></div>
        <div class="stat"><div class="stat-label">High Priority</div><div class="stat-value">{sum(1 for item in items if item.get('priority_level') == 'high')}</div></div>
        <div class="stat"><div class="stat-label">Unresolved</div><div class="stat-value">{len(unresolved_items)}</div></div>
      </div>
    </section>
    <section class="queue-layout">
      <div class="section">
        <h2>Action Queue</h2>
        <p>Start here when you only have time to fix the next few incidents. Baseline regressions rise to the top automatically.</p>
        <div class="mini-grid">{queue_cards}</div>
      </div>
    </section>
    <section class="focus-layout">
      <div class="section">
        <h2>Focus Views</h2>
        <p>Use these counts to decide whether the team should regression-triage, pick up unassigned work, or finish what is already in progress.</p>
        <div class="mini-grid">{focus_cards}</div>
      </div>
      <div class="section">
        <h2>Owner Load</h2>
        <p>Simple owner-centric slice so you can spot uneven incident load without opening every case file.</p>
        <div class="mini-grid">{owner_cards}</div>
      </div>
    </section>
    <section class="layout">
      <div class="section">
        <h2>Recurring Issue Leaderboard</h2>
        <p>The failure fingerprints creating the most repeated debugging work right now.</p>
        <div class="mini-grid">{leaderboard_cards}</div>
      </div>
      <div class="section">
        <h2>Trend Watch</h2>
        <p>Which failure fingerprints are rising in the most recent runs.</p>
        <div class="mini-grid">{trend_cards}</div>
      </div>
        <div class="section">
          <h2>Top Cases</h2>
          <p>Start with the highest-value incidents first, especially baseline regressions.</p>
          <p>Status mix: {html.escape(', '.join(f'{key}={value}' for key, value in sorted(statuses.items())) or 'none')}</p>
          <div class="case-stack">{case_cards}</div>
        </div>
      </section>
      <section class="gate-layout">
        <div class="section">
          <h2>Benchmark Gate</h2>
          <p>Regression-proof detection matters. Keep benchmark coverage visible on the same reliability homepage.</p>
          <div class="mini-grid">
            <div class="mini-card">
              <div class="mini-label">Coverage</div>
              <div class="mini-value">matched {html.escape(str(coverage.get('matched', 0)))}</div>
              <div class="mini-meta">partial {html.escape(str(coverage.get('partial', 0)))} · missed {html.escape(str(coverage.get('missed', 0)))}</div>
            </div>
            <div class="mini-card">
              <div class="mini-label">Regression Gate</div>
              <div class="mini-value">{html.escape(str(gate.get('regressions', 0)))} regressions</div>
              <div class="mini-meta">baseline {html.escape(str(gate.get('baseline_name') or 'not configured'))}</div>
            </div>
            <div class="mini-card">
              <div class="mini-label">Reports</div>
              <div class="mini-value">{html.escape(str(coverage.get('fixtures', 0)))} fixtures</div>
              <div class="mini-meta">coverage {html.escape(str(gate.get('report_path') or 'n/a'))}</div>
              <div class="mini-meta">regression {html.escape(str(gate.get('regression_report_path') or 'n/a'))}</div>
            </div>
          </div>
        </div>
        <div class="section">
          <h2>Regression Watchlist</h2>
          <p>The fixtures that slipped from matched coverage and should block confidence in new agent changes.</p>
          <div class="mini-grid">{gate_cards}</div>
        </div>
      </section>
  </main>
</body>
</html>
'''


def write_case_board(items: list[dict[str, Any]]) -> Path:
    CASEFILES_DIR.mkdir(parents=True, exist_ok=True)
    CASE_BOARD_OUT.write_text(build_case_board_html(items, benchmark_gate=collect_benchmark_gate_status()), encoding='utf-8')
    return CASE_BOARD_OUT
