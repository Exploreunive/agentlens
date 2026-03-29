from __future__ import annotations

import html
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

FINGERPRINTS_DIR = Path('artifacts/fingerprints')
FINGERPRINT_INDEX_OUT = FINGERPRINTS_DIR / 'index.html'


def fingerprint_slug(label: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', str(label or 'unknown-failure').lower()).strip('-')
    return slug or 'unknown-failure'


def fingerprint_report_path(label: str) -> Path:
    return FINGERPRINTS_DIR / f'{fingerprint_slug(label)}.html'


def _item_label(item: dict[str, Any]) -> str:
    return str(
        (item.get('failure_fingerprint') or {}).get('label')
        or item.get('failure_mode')
        or 'unknown_failure'
    )


def _workflow_state(item: dict[str, Any]) -> str:
    return str(item.get('case_workflow_state') or item.get('workflow_state') or item.get('case_status') or 'new')


def _resolved_state(item: dict[str, Any]) -> bool:
    return _workflow_state(item) in {'verified', 'ignored'}


def _pick_playbook(group: list[dict[str, Any]]) -> tuple[str, str]:
    verified_steps = [
        str(item.get('case_next_step')).strip()
        for item in group
        if _workflow_state(item) == 'verified' and str(item.get('case_next_step') or '').strip()
    ]
    if verified_steps:
        step, count = Counter(verified_steps).most_common(1)[0]
        suffix = 'reused across verified fixes' if count > 1 else 'from the latest verified repair path'
        return step, suffix

    all_steps = [
        str(item.get('case_next_step')).strip()
        for item in group
        if str(item.get('case_next_step') or '').strip()
    ]
    if all_steps:
        step, count = Counter(all_steps).most_common(1)[0]
        suffix = 'repeated across active incidents' if count > 1 else 'from the current incident workflow'
        return step, suffix

    regressions = sum(1 for item in group if item.get('regression_detected'))
    if regressions:
        return (
            'Diff the latest regressed trace against baseline and isolate the first changed decision.',
            'fallback generated from regression watch',
        )
    return (
        'Open the representative trace and confirm the first unsupported decision before changing heuristics.',
        'fallback generated from trace review workflow',
    )


def build_fingerprint_dossiers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[_item_label(item)].append(item)

    dossiers: list[dict[str, Any]] = []
    for label, group in grouped.items():
        ordered = sorted(
            group,
            key=lambda item: (
                int(item.get('trace_recency_rank', 999999)),
                -int(item.get('priority_score', 0)),
                str(item.get('trace_file')),
            ),
        )
        owners = Counter(str(item.get('case_owner') or 'unassigned') for item in ordered)
        states = Counter(_workflow_state(item) for item in ordered)
        playbook, playbook_source = _pick_playbook(ordered)
        representative = ordered[0]
        latest_verified = next((item for item in ordered if _workflow_state(item) == 'verified'), None)
        latest_reopened = next((item for item in ordered if _workflow_state(item) == 'reopened'), None)
        latest_unresolved = next((item for item in ordered if not _resolved_state(item)), None)
        regressions = sum(1 for item in ordered if item.get('regression_detected'))
        reopened = states.get('reopened', 0)
        verified = states.get('verified', 0)
        unresolved = sum(1 for item in ordered if not _resolved_state(item))
        if reopened and not verified:
            impact_summary = f'Reopened {reopened} time(s) without a verified repair yet.'
        elif reopened > verified:
            impact_summary = f'Reopened {reopened} time(s); only {verified} verified repair(s) have been recorded.'
        elif reopened:
            impact_summary = f'{verified} verified repair(s) recorded after {reopened} reopening(s).'
        elif regressions:
            impact_summary = f'{regressions} baseline regression(s) are attached to this fingerprint right now.'
        else:
            impact_summary = 'No reopenings yet; watch the next incident for repair durability.'
        dossiers.append(
            {
                'label': label,
                'slug': fingerprint_slug(label),
                'path': str(fingerprint_report_path(label)),
                'count': len(ordered),
                'regressions': regressions,
                'reopened': reopened,
                'verified': verified,
                'unresolved': unresolved,
                'owners': owners,
                'owner_summary': ', '.join(f'{owner} ({count})' for owner, count in owners.most_common(3)),
                'states': states,
                'playbook': playbook,
                'playbook_source': playbook_source,
                'impact_summary': impact_summary,
                'representative_trace': str(representative.get('trace_file') or 'n/a'),
                'representative_case_path': str(representative.get('case_index_path') or ''),
                'representative_trace_path': str(representative.get('trace_view_path') or ''),
                'latest_verified_step': str(latest_verified.get('case_next_step')) if latest_verified else '',
                'latest_reopened_trace': str(latest_reopened.get('trace_file') or '') if latest_reopened else '',
                'active_owner': str(latest_unresolved.get('case_owner') or 'unassigned') if latest_unresolved else 'unassigned',
                'items': ordered,
            }
        )
    dossiers.sort(
        key=lambda row: (
            -int(row.get('reopened', 0)),
            -int(row.get('regressions', 0)),
            -int(row.get('unresolved', 0)),
            -int(row.get('count', 0)),
            str(row.get('label')),
        )
    )
    return dossiers


def build_fingerprint_index_html(dossiers: list[dict[str, Any]]) -> str:
    cards = ''.join(
        f'''
        <section class="card">
          <div class="card-head">
            <div>
              <div class="eyebrow">Fingerprint dossier</div>
              <h2>{html.escape(str(row["label"]))}</h2>
            </div>
            <div class="score">{html.escape(str(row["count"]))}</div>
          </div>
          <div class="meta">
            <span>unresolved: <strong>{html.escape(str(row["unresolved"]))}</strong></span>
            <span>reopened: <strong>{html.escape(str(row["reopened"]))}</strong></span>
            <span>regressions: <strong>{html.escape(str(row["regressions"]))}</strong></span>
            <span>verified: <strong>{html.escape(str(row["verified"]))}</strong></span>
          </div>
          <div class="playbook">{html.escape(str(row["playbook"]))}</div>
          <div class="hint">Playbook source: {html.escape(str(row["playbook_source"]))}</div>
          <div class="hint">Owners: {html.escape(str(row["owner_summary"] or "unassigned"))}</div>
          <div class="hint">Representative trace: <code>{html.escape(str(row["representative_trace"]))}</code></div>
          <div class="hint">Open dossier: <code>{html.escape(str(row["path"]))}</code></div>
        </section>
        '''
        for row in dossiers
    ) or '<div class="empty">No recurring fingerprints found yet.</div>'

    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Fingerprint Dossiers</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07101d;
      --panel: rgba(14, 24, 40, 0.92);
      --border: #22324f;
      --text: #edf3fb;
      --muted: #9fb0c8;
      --accent: #7cc4ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #132440 0%, var(--bg) 60%); color: var(--text); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 40px 24px 64px; }}
    .hero, .card, .stat {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; }}
    .hero, .card {{ padding: 20px; }}
    .hero {{ margin-bottom: 18px; }}
    .stats, .stack {{ display: grid; gap: 14px; }}
    .stats {{ grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 18px; }}
    .stat {{ padding: 16px; }}
    .label, .eyebrow {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 16px; }}
    h1, h2 {{ margin: 0; }}
    p, .meta, .hint {{ color: var(--muted); }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 18px; margin: 14px 0; }}
    .playbook {{ margin-top: 8px; padding: 14px; border-radius: 14px; background: #0c1524; border: 1px solid var(--border); line-height: 1.6; }}
    .hint {{ margin-top: 8px; }}
    .score {{ min-width: 58px; height: 58px; border-radius: 16px; display: grid; place-items: center; font-size: 22px; font-weight: 800; background: #0d1728; border: 1px solid var(--border); }}
    code {{ color: var(--accent); font-family: ui-monospace, SFMono-Regular, monospace; }}
    .empty {{ color: var(--muted); }}
    @media (max-width: 900px) {{ .stats {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>AgentLens Fingerprint Dossiers</h1>
      <p>Recurring agent failures turned into reusable repair context: which failures repeat, which fixes actually held, and which ones reopened.</p>
    </section>
    <section class="stats">
      <div class="stat"><div class="label">Fingerprints</div><div class="value">{len(dossiers)}</div></div>
      <div class="stat"><div class="label">Reopened</div><div class="value">{sum(int(row.get("reopened", 0)) for row in dossiers)}</div></div>
      <div class="stat"><div class="label">Regressions</div><div class="value">{sum(int(row.get("regressions", 0)) for row in dossiers)}</div></div>
      <div class="stat"><div class="label">Verified Fixes</div><div class="value">{sum(int(row.get("verified", 0)) for row in dossiers)}</div></div>
    </section>
    <section class="stack">{cards}</section>
  </main>
</body>
</html>
'''


def build_fingerprint_detail_html(dossier: dict[str, Any]) -> str:
    states = ', '.join(f'{state}={count}' for state, count in sorted((dossier.get('states') or {}).items())) or 'none'
    cases = ''.join(
        f'''
        <section class="case">
          <div class="case-head">
            <div>
              <div class="eyebrow">{html.escape(_workflow_state(item))}</div>
              <h2>{html.escape(str(item.get("trace_file") or "n/a"))}</h2>
            </div>
            <div class="score">{html.escape(str(item.get("priority_score", 0)))}</div>
          </div>
          <div class="meta">
            <span>owner: <strong>{html.escape(str(item.get("case_owner") or "unassigned"))}</strong></span>
            <span>baseline: <strong>{html.escape("regressed" if item.get("regression_detected") else "clean")}</strong></span>
            <span>risk: <strong>{html.escape(str(item.get("answer_risk") or "unknown"))}</strong></span>
          </div>
          <div class="playbook">{html.escape(str(item.get("case_next_step") or "No next step recorded."))}</div>
          <div class="hint">Case file: <code>{html.escape(str(item.get("case_index_path") or ""))}</code></div>
          <div class="hint">Trace page: <code>{html.escape(str(item.get("trace_view_path") or ""))}</code></div>
        </section>
        '''
        for item in dossier.get('items', [])
    ) or '<div class="empty">No representative cases yet.</div>'

    latest_verified_step = str(dossier.get('latest_verified_step') or '').strip()
    durability_note = (
        f'Latest verified repair step: {latest_verified_step}'
        if latest_verified_step
        else 'No verified repair has been recorded for this fingerprint yet.'
    )

    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Fingerprint Dossier · {html.escape(str(dossier.get("label") or "unknown"))}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07101d;
      --panel: rgba(14, 24, 40, 0.92);
      --border: #22324f;
      --text: #edf3fb;
      --muted: #9fb0c8;
      --accent: #7cc4ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #132440 0%, var(--bg) 60%); color: var(--text); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 40px 24px 64px; }}
    .hero, .card, .case {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; }}
    .hero, .card, .case {{ padding: 20px; }}
    .hero {{ margin-bottom: 18px; }}
    .grid, .stack {{ display: grid; gap: 14px; }}
    .grid {{ grid-template-columns: 1.2fr 1.8fr; margin-bottom: 18px; }}
    .eyebrow {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .case-head {{ display: flex; justify-content: space-between; gap: 16px; }}
    h1, h2 {{ margin: 0; }}
    p, .meta, .hint {{ color: var(--muted); }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 18px; margin: 14px 0; }}
    .playbook {{ margin-top: 8px; padding: 14px; border-radius: 14px; background: #0c1524; border: 1px solid var(--border); line-height: 1.6; }}
    .hint {{ margin-top: 8px; }}
    .score {{ min-width: 58px; height: 58px; border-radius: 16px; display: grid; place-items: center; font-size: 22px; font-weight: 800; background: #0d1728; border: 1px solid var(--border); }}
    code {{ color: var(--accent); font-family: ui-monospace, SFMono-Regular, monospace; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="eyebrow">Fingerprint dossier</div>
      <h1>{html.escape(str(dossier.get("label") or "unknown"))}</h1>
      <p>State mix: {html.escape(states)}</p>
    </section>
    <section class="grid">
      <div class="card">
        <div class="eyebrow">Recommended playbook</div>
        <div class="playbook">{html.escape(str(dossier.get("playbook") or ""))}</div>
        <div class="hint">Source: {html.escape(str(dossier.get("playbook_source") or "unknown"))}</div>
        <div class="hint">{html.escape(durability_note)}</div>
      </div>
      <div class="card">
        <div class="eyebrow">Operational summary</div>
        <div class="meta">
          <span>cases: <strong>{html.escape(str(dossier.get("count", 0)))}</strong></span>
          <span>unresolved: <strong>{html.escape(str(dossier.get("unresolved", 0)))}</strong></span>
          <span>reopened: <strong>{html.escape(str(dossier.get("reopened", 0)))}</strong></span>
          <span>regressions: <strong>{html.escape(str(dossier.get("regressions", 0)))}</strong></span>
          <span>verified: <strong>{html.escape(str(dossier.get("verified", 0)))}</strong></span>
        </div>
        <div class="hint">Owners: {html.escape(str(dossier.get("owner_summary") or "unassigned"))}</div>
        <div class="hint">Representative trace: <code>{html.escape(str(dossier.get("representative_trace") or "n/a"))}</code></div>
      </div>
    </section>
    <section class="stack">{cases}</section>
  </main>
</body>
</html>
'''


def write_fingerprint_reports(items: list[dict[str, Any]]) -> tuple[Path, list[Path]]:
    dossiers = build_fingerprint_dossiers(items)
    FINGERPRINTS_DIR.mkdir(parents=True, exist_ok=True)
    detail_paths: list[Path] = []
    for dossier in dossiers:
        out = fingerprint_report_path(str(dossier.get('label') or 'unknown-failure'))
        out.write_text(build_fingerprint_detail_html(dossier), encoding='utf-8')
        detail_paths.append(out)
    FINGERPRINT_INDEX_OUT.write_text(build_fingerprint_index_html(dossiers), encoding='utf-8')
    return FINGERPRINT_INDEX_OUT, detail_paths
