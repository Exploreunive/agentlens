from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from regression import BASELINE_DIR, build_regression_report, list_traces, load_baseline, save_baseline, summarize_regression, load_trace

ROOT = Path(__file__).resolve().parent


def _run(script: str) -> int:
    return subprocess.call([sys.executable, str(ROOT / script)])


def cmd_demo(args: argparse.Namespace) -> int:
    demo_map = {
        'minimal': 'examples/minimal_agent.py',
        'divergent': 'examples/divergent_agent.py',
        'failure': 'examples/failure_answer_agent.py',
        'openai-wrapper': 'examples/openai_wrapper_demo.py',
    }
    return _run(demo_map[args.scenario])


def cmd_view(_: argparse.Namespace) -> int:
    return _run('viewer.py')


def cmd_diff(_: argparse.Namespace) -> int:
    return _run('diff_runs.py')


def cmd_explain(_: argparse.Namespace) -> int:
    view_code = _run('viewer.py')
    if view_code != 0:
        return view_code
    return _run('diff_runs.py')


def cmd_baseline_save(args: argparse.Namespace) -> int:
    traces = list_traces()
    if not traces:
        raise SystemExit('No traces available to save as a baseline')
    saved = save_baseline(args.name, traces[0])
    print(f'Saved baseline {args.name} -> {saved}')
    return 0


def cmd_baseline_list(_: argparse.Namespace) -> int:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    baselines = sorted(BASELINE_DIR.glob('*.json'))
    if not baselines:
        print('No baselines saved yet')
        return 0
    for path in baselines:
        print(path.stem)
    return 0


def cmd_regression_check(args: argparse.Namespace) -> int:
    baseline_trace_path, baseline_events = load_baseline(args.name)
    traces = list_traces()
    if not traces:
        raise SystemExit('No candidate traces available')
    candidate_trace = traces[0]
    candidate_events = load_trace(candidate_trace)
    summary = summarize_regression(baseline_events, candidate_events)
    report = build_regression_report(args.name, baseline_trace_path.name, candidate_trace.name, summary)

    out = ROOT / 'artifacts' / f'regression_{args.name}.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding='utf-8')
    print(f'Wrote {out}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='agentlens',
        description='Local-first debugging workspace for LLM agent failures.',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_demo = sub.add_parser('demo', help='run an example scenario and emit trace(s)')
    p_demo.add_argument(
        'scenario',
        nargs='?',
        default='minimal',
        choices=['minimal', 'divergent', 'failure', 'openai-wrapper'],
        help='which built-in scenario to run (default: minimal)',
    )
    p_demo.set_defaults(func=cmd_demo)

    p_view = sub.add_parser('view', help='render the latest trace to HTML')
    p_view.set_defaults(func=cmd_view)

    p_diff = sub.add_parser('diff', help='compare the two latest runs and write a Markdown report')
    p_diff.set_defaults(func=cmd_diff)

    p_explain = sub.add_parser(
        'explain',
        help='generate both the latest HTML trace view and the latest Markdown diff report',
    )
    p_explain.set_defaults(func=cmd_explain)

    p_baseline = sub.add_parser('baseline', help='manage named baseline traces')
    baseline_sub = p_baseline.add_subparsers(dest='baseline_command', required=True)

    p_baseline_save = baseline_sub.add_parser('save', help='save the latest trace as a named baseline')
    p_baseline_save.add_argument('name', help='baseline name')
    p_baseline_save.set_defaults(func=cmd_baseline_save)

    p_baseline_list = baseline_sub.add_parser('list', help='list saved baselines')
    p_baseline_list.set_defaults(func=cmd_baseline_list)

    p_regression = sub.add_parser('regression', help='compare the latest run against a saved baseline')
    regression_sub = p_regression.add_subparsers(dest='regression_command', required=True)

    p_regression_check = regression_sub.add_parser('check', help='write a regression report for the latest candidate run')
    p_regression_check.add_argument('name', help='saved baseline name')
    p_regression_check.set_defaults(func=cmd_regression_check)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
