from __future__ import annotations

from pathlib import Path

from benchmark_report import build_benchmark_regression_report, build_benchmark_regression_summary, build_benchmark_report, collect_benchmark_cases, save_benchmark_baseline, summarize_benchmark_coverage, write_benchmark_regression_report, write_benchmark_report


def test_collect_benchmark_cases_loads_fixture_summaries():
    items = collect_benchmark_cases()
    names = {item['fixture'] for item in items}
    assert 'wrong_tool_selected.jsonl' in names
    assert 'tool_result_ignored.jsonl' in names
    assert all(item.get('coverage_status') == 'matched' for item in items)


def test_build_benchmark_report_contains_expected_sections():
    report = build_benchmark_report([
        {
            'fixture': 'wrong_tool_selected.jsonl',
            'expected': {
                'failure_mode': 'wrong_tool_selected',
                'fingerprint': 'wrong-tool-selected',
                'signal': 'used_wrong_tool',
            },
            'coverage_status': 'matched',
            'matched_fields': ['failure_mode', 'fingerprint', 'signal'],
            'missed_fields': [],
            'failure_mode': 'wrong_tool_selected',
            'fingerprint': 'wrong-tool-selected',
            'priority_level': 'high',
            'priority_score': 95,
            'answer_risk': 'hidden_degradation',
            'signal': 'used_wrong_tool',
            'final_answer': 'Done.',
        }
    ])
    assert 'AgentLens Benchmark Coverage Report' in report
    assert 'wrong_tool_selected' in report
    assert 'wrong-tool-selected' in report
    assert 'coverage_status: `matched`' in report


def test_write_benchmark_report_creates_markdown_and_html(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        (tmp_path / 'tests' / 'fixtures' / 'benchmarks').mkdir(parents=True)
        source_dir = Path(__file__).resolve().parent / 'fixtures' / 'benchmarks'
        for fixture in source_dir.glob('*.jsonl'):
            (tmp_path / 'tests' / 'fixtures' / 'benchmarks' / fixture.name).write_text(
                fixture.read_text(encoding='utf-8'),
                encoding='utf-8',
            )
        md_out, html_out = write_benchmark_report()
    finally:
        os.chdir(previous_cwd)

    assert (tmp_path / md_out).exists()
    assert (tmp_path / html_out).exists()
    assert 'AgentLens Benchmark Coverage' in (tmp_path / html_out).read_text(encoding='utf-8')
    assert 'Matched' in (tmp_path / html_out).read_text(encoding='utf-8')


def test_build_benchmark_regression_report_detects_coverage_drop():
    report = build_benchmark_regression_report(
        'golden',
        [{'fixture': 'wrong_tool_selected.jsonl', 'coverage_status': 'matched', 'fingerprint': 'wrong-tool-selected'}],
        [{'fixture': 'wrong_tool_selected.jsonl', 'coverage_status': 'partial', 'fingerprint': 'wrong-tool-selected'}],
    )
    assert 'AgentLens Benchmark Regression Report' in report
    assert 'coverage_before: `matched`' in report
    assert 'coverage_after: `partial`' in report
    assert '- regressions: `1`' in report


def test_benchmark_summary_helpers_capture_coverage_and_regressions():
    coverage = summarize_benchmark_coverage([
        {'coverage_status': 'matched'},
        {'coverage_status': 'partial'},
        {'coverage_status': 'missed'},
    ])
    summary = build_benchmark_regression_summary(
        'golden',
        [{'fixture': 'wrong_tool_selected.jsonl', 'coverage_status': 'matched', 'fingerprint': 'wrong-tool-selected'}],
        [{'fixture': 'wrong_tool_selected.jsonl', 'coverage_status': 'partial', 'fingerprint': 'wrong-tool-selected'}],
    )
    assert coverage == {'fixtures': 3, 'matched': 1, 'partial': 1, 'missed': 1}
    assert summary['baseline_name'] == 'golden'
    assert summary['regressions'] == 1
    assert summary['regressed_fixtures'][0]['fixture'] == 'wrong_tool_selected.jsonl'


def test_save_and_check_benchmark_baseline_round_trip(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        fixtures_dir = tmp_path / 'tests' / 'fixtures' / 'benchmarks'
        fixtures_dir.mkdir(parents=True)
        source_dir = Path(__file__).resolve().parent / 'fixtures' / 'benchmarks'
        for fixture in source_dir.glob('*.jsonl'):
            (fixtures_dir / fixture.name).write_text(fixture.read_text(encoding='utf-8'), encoding='utf-8')
        baseline = save_benchmark_baseline('golden')
        report = write_benchmark_regression_report('golden')
    finally:
        os.chdir(previous_cwd)

    assert (tmp_path / baseline).exists()
    assert (tmp_path / report).exists()
    assert 'AgentLens Benchmark Regression Report' in (tmp_path / report).read_text(encoding='utf-8')
