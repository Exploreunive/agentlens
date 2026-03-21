from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def cmd_demo(_: argparse.Namespace) -> int:
    return subprocess.call([sys.executable, str(ROOT / 'examples' / 'minimal_agent.py')])


def cmd_view(_: argparse.Namespace) -> int:
    return subprocess.call([sys.executable, str(ROOT / 'viewer.py')])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='agentlens')
    sub = parser.add_subparsers(dest='command', required=True)

    p_demo = sub.add_parser('demo', help='run the minimal example and emit a trace')
    p_demo.set_defaults(func=cmd_demo)

    p_view = sub.add_parser('view', help='render latest trace to HTML')
    p_view.set_defaults(func=cmd_view)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
