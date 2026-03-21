from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(script: str) -> int:
    return subprocess.call([sys.executable, str(ROOT / script)])


def cmd_demo(args: argparse.Namespace) -> int:
    demo_map = {
        'minimal': 'examples/minimal_agent.py',
        'divergent': 'examples/divergent_agent.py',
        'failure': 'examples/failure_answer_agent.py',
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
        choices=['minimal', 'divergent', 'failure'],
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
