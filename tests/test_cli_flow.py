from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cli_demo_and_view(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    view = subprocess.run([sys.executable, 'cli.py', 'view'], cwd=work, capture_output=True, text=True)
    assert view.returncode == 0, view.stderr

    traces = list((work / '.agentlens' / 'traces').glob('*.jsonl'))
    assert traces, 'expected at least one trace file'

    html_file = work / 'artifacts' / 'latest_trace.html'
    assert html_file.exists()
    html = html_file.read_text(encoding='utf-8')
    assert 'AgentLens Trace Viewer' in html


def test_cli_view_supports_specific_trace(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'minimal'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    traces = sorted((work / '.agentlens' / 'traces').glob('*.jsonl'))
    assert traces
    trace_stem = traces[0].stem

    view = subprocess.run([sys.executable, 'cli.py', 'view', trace_stem], cwd=work, capture_output=True, text=True)
    assert view.returncode == 0, view.stderr

    html_file = work / 'artifacts' / 'views' / f'{trace_stem}.html'
    assert html_file.exists()
    assert 'AgentLens Trace Viewer' in html_file.read_text(encoding='utf-8')


def test_cli_supports_divergent_diff_and_explain(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'divergent'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    diff = subprocess.run([sys.executable, 'cli.py', 'diff'], cwd=work, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stderr

    explain = subprocess.run([sys.executable, 'cli.py', 'explain'], cwd=work, capture_output=True, text=True)
    assert explain.returncode == 0, explain.stderr

    diff_file = work / 'artifacts' / 'latest_diff.md'
    html_file = work / 'artifacts' / 'latest_trace.html'
    assert diff_file.exists()
    assert html_file.exists()

    diff_text = diff_file.read_text(encoding='utf-8')
    html_text = html_file.read_text(encoding='utf-8')
    assert 'AgentLens Run Divergence' in diff_text
    assert 'AgentLens Trace Viewer' in html_text


def test_cli_supports_baseline_and_regression_workflow(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    baseline_demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'minimal'], cwd=work, capture_output=True, text=True)
    assert baseline_demo.returncode == 0, baseline_demo.stderr

    baseline_save = subprocess.run([sys.executable, 'cli.py', 'baseline', 'save', 'golden-run'], cwd=work, capture_output=True, text=True)
    assert baseline_save.returncode == 0, baseline_save.stderr

    baseline_list = subprocess.run([sys.executable, 'cli.py', 'baseline', 'list'], cwd=work, capture_output=True, text=True)
    assert baseline_list.returncode == 0, baseline_list.stderr
    assert 'golden-run' in baseline_list.stdout

    candidate_demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'failure'], cwd=work, capture_output=True, text=True)
    assert candidate_demo.returncode == 0, candidate_demo.stderr

    regression = subprocess.run([sys.executable, 'cli.py', 'regression', 'check', 'golden-run'], cwd=work, capture_output=True, text=True)
    assert regression.returncode == 0, regression.stderr

    reports = list((work / 'artifacts' / 'regressions').glob('golden-run__*.md'))
    assert reports
    text = reports[0].read_text(encoding='utf-8')
    assert 'AgentLens Regression Report' in text
    assert 'regression_detected' in text
    assert 'baseline: `golden-run`' in text
    assert 'candidate:' in text


def test_cli_supports_bundle_export(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'minimal'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    bundle = subprocess.run([sys.executable, 'cli.py', 'bundle', 'export'], cwd=work, capture_output=True, text=True)
    assert bundle.returncode == 0, bundle.stderr
    assert 'artifacts/bundles' in bundle.stdout


def test_cli_supports_debug_inbox(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'divergent'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    inbox = subprocess.run([sys.executable, 'cli.py', 'inbox'], cwd=work, capture_output=True, text=True)
    assert inbox.returncode == 0, inbox.stderr
    assert 'debug_inbox.md' in inbox.stdout
    assert 'debug_inbox.html' in inbox.stdout
    report = work / 'artifacts' / 'debug_inbox.md'
    html_report = work / 'artifacts' / 'debug_inbox.html'
    trace_views_dir = work / 'artifacts' / 'views'
    case_board = work / 'artifacts' / 'cases' / 'index.html'
    assert report.exists()
    assert html_report.exists()
    assert case_board.exists()
    assert any(trace_views_dir.glob('*.html'))
    assert 'AgentLens Debug Inbox' in report.read_text(encoding='utf-8')
    assert 'AgentLens Debug Inbox' in html_report.read_text(encoding='utf-8')
    assert 'AgentLens Incident Board' in case_board.read_text(encoding='utf-8')


def test_cli_inbox_supports_baseline_watch(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    baseline_demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'minimal'], cwd=work, capture_output=True, text=True)
    assert baseline_demo.returncode == 0, baseline_demo.stderr

    baseline_save = subprocess.run([sys.executable, 'cli.py', 'baseline', 'save', 'golden-run'], cwd=work, capture_output=True, text=True)
    assert baseline_save.returncode == 0, baseline_save.stderr

    candidate_demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'failure'], cwd=work, capture_output=True, text=True)
    assert candidate_demo.returncode == 0, candidate_demo.stderr

    inbox = subprocess.run([sys.executable, 'cli.py', 'inbox', '--baseline', 'golden-run'], cwd=work, capture_output=True, text=True)
    assert inbox.returncode == 0, inbox.stderr

    report = work / 'artifacts' / 'debug_inbox.md'
    html_report = work / 'artifacts' / 'debug_inbox.html'
    regression_reports_dir = work / 'artifacts' / 'regressions'
    assert 'Active baseline: `golden-run`.' in report.read_text(encoding='utf-8')
    assert 'Baseline watch: golden-run' in html_report.read_text(encoding='utf-8')
    assert any(regression_reports_dir.glob('golden-run__*.md'))


def test_cli_supports_benchmark_report(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    report = subprocess.run([sys.executable, 'cli.py', 'bench', 'report'], cwd=work, capture_output=True, text=True)
    assert report.returncode == 0, report.stderr
    assert 'benchmark_report.md' in report.stdout
    assert 'benchmark_report.html' in report.stdout

    md_file = work / 'artifacts' / 'benchmark_report.md'
    html_file = work / 'artifacts' / 'benchmark_report.html'
    assert md_file.exists()
    assert html_file.exists()
    assert 'AgentLens Benchmark Coverage Report' in md_file.read_text(encoding='utf-8')


def test_cli_supports_benchmark_baseline_and_check(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    save = subprocess.run([sys.executable, 'cli.py', 'bench', 'baseline', 'save', 'golden'], cwd=work, capture_output=True, text=True)
    assert save.returncode == 0, save.stderr
    assert 'Saved benchmark baseline golden' in save.stdout

    check = subprocess.run([sys.executable, 'cli.py', 'bench', 'check', 'golden'], cwd=work, capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    assert 'benchmark_regression.md' in check.stdout

    regression_file = work / 'artifacts' / 'benchmark_regression.md'
    assert regression_file.exists()
    assert 'AgentLens Benchmark Regression Report' in regression_file.read_text(encoding='utf-8')


def test_cli_supports_case_update(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    demo = subprocess.run([sys.executable, 'cli.py', 'demo', 'failure'], cwd=work, capture_output=True, text=True)
    assert demo.returncode == 0, demo.stderr

    inbox = subprocess.run([sys.executable, 'cli.py', 'inbox'], cwd=work, capture_output=True, text=True)
    assert inbox.returncode == 0, inbox.stderr

    case_update = subprocess.run(
        [
            sys.executable,
            'cli.py',
            'case',
            'update',
            'latest',
            '--status',
            'investigating',
            '--owner',
            'alice',
            '--next-step',
            'Replay the failing tool call with fixed inputs.',
        ],
        cwd=work,
        capture_output=True,
        text=True,
    )
    assert case_update.returncode == 0, case_update.stderr
    assert 'Updated artifacts/cases/latest/README.md' not in case_update.stdout

    updated_path = case_update.stdout.strip().split('Updated ', 1)[1]
    readme = work / updated_path
    text = readme.read_text(encoding='utf-8')
    assert '- status: `investigating`' in text
    assert '- owner: `alice`' in text
    assert '- next_step: `Replay the failing tool call with fixed inputs.`' in text
