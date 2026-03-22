from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from analyzer import summarize_divergence

TRACE_DIR = Path('.agentlens/traces')
OUT = Path('artifacts/latest_diff.md')


def load_two_latest() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, str]:
    files = sorted(TRACE_DIR.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    if len(files) < 2:
        raise SystemExit('Need at least two trace files to diff')
    a_file, b_file = files[1], files[0]

    def load(path: Path) -> List[Dict[str, Any]]:
        items = []
        with path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    a = load(a_file)
    b = load(b_file)
    return a, b, a_file.name, b_file.name


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_type: Dict[str, int] = {}
    tool_names = []
    final_answer = None
    memory_writes = []
    for e in events:
        et = e.get('type', 'unknown')
        by_type[et] = by_type.get(et, 0) + 1
        if et == 'tool.call':
            tool_name = (e.get('payload') or {}).get('tool_name')
            if tool_name:
                tool_names.append(tool_name)
        if et == 'memory.write':
            content = (e.get('payload') or {}).get('content')
            if content:
                memory_writes.append(content)
        if et == 'run.end':
            final_answer = (e.get('payload') or {}).get('final_answer')
    return {
        'event_counts': by_type,
        'tool_names': tool_names,
        'memory_writes': memory_writes,
        'final_answer': final_answer,
    }


def _format_timeline(divergence: Dict[str, Any]) -> str:
    timeline = divergence.get('divergence_timeline') or []
    if not timeline:
        return '- no divergence detected'
    lines = []
    for step in timeline[:6]:
        lines.append(
            f"- event #{step.get('event_index')}: {step.get('difference_kind')} | "
            f"A={step.get('a_type')} {step.get('a_payload')} | "
            f"B={step.get('b_type')} {step.get('b_payload')}"
        )
    return '\n'.join(lines)


def build_report(a_name: str, b_name: str, a_sum: Dict[str, Any], b_sum: Dict[str, Any], divergence: Dict[str, Any]) -> str:
    lines = []
    lines.append('# AgentLens Run Divergence\n')
    lines.append(f'- A: `{a_name}`')
    lines.append(f'- B: `{b_name}`')
    lines.append(f"- severity: `{divergence.get('severity')}`")
    lines.append(f"- divergence_count: `{divergence.get('divergence_count')}`\n")
    lines.append('## First divergence')
    lines.append(f"- {divergence.get('first_divergence')}\n")
    lines.append('## Divergence timeline')
    lines.append(_format_timeline(divergence) + '\n')
    lines.append('## Final answer')
    lines.append(f'- A: {a_sum.get("final_answer")}')
    lines.append(f'- B: {b_sum.get("final_answer")}')
    lines.append(f"- A answer risk: {divergence.get('a_answer_risk')}")
    lines.append(f"- B answer risk: {divergence.get('b_answer_risk')}\n")
    lines.append('## Suspicious signals')
    lines.append(f'- A: {divergence.get("a_suspicious_signals", [])}')
    lines.append(f'- B: {divergence.get("b_suspicious_signals", [])}\n')
    lines.append('## Tool calls')
    lines.append(f'- A: {a_sum.get("tool_names", [])}')
    lines.append(f'- B: {b_sum.get("tool_names", [])}\n')
    lines.append('## Memory writes')
    lines.append(f'- A: {a_sum.get("memory_writes", [])}')
    lines.append(f'- B: {b_sum.get("memory_writes", [])}\n')
    lines.append('## Event counts')
    lines.append(f'- A: {a_sum.get("event_counts", {})}')
    lines.append(f'- B: {b_sum.get("event_counts", {})}')
    return '\n'.join(lines) + '\n'


def main() -> None:
    a, b, a_name, b_name = load_two_latest()
    report = build_report(a_name, b_name, summarize(a), summarize(b), summarize_divergence(a, b))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report, encoding='utf-8')
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
