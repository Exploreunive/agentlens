from __future__ import annotations

from pathlib import Path

from benchmark_report import build_benchmark_report, collect_benchmark_cases, write_benchmark_report


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
