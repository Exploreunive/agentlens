from __future__ import annotations

import json
from pathlib import Path

from agentlens import AgentLensClient
from agentlens.langgraph_adapter import AgentLensLangGraphAgent


class _FakeMessage:
    def __init__(self, content: str, *, response_metadata: dict | None = None, usage_metadata: dict | None = None, tool_calls: list | None = None):
        self.content = content
        self.response_metadata = response_metadata or {}
        self.usage_metadata = usage_metadata or {}
        self.tool_calls = tool_calls or []


class _FakeAgent:
    def __init__(self, response: dict):
        self.response = response

    def invoke(self, payload: dict) -> dict:
        assert 'messages' in payload
        return self.response


def test_langgraph_adapter_invoke_emits_run_boundaries(tmp_path: Path, monkeypatch):
    storage = tmp_path / 'traces'
    client = AgentLensClient(str(storage))

    fake_result = {
        'messages': [
            _FakeMessage('Should I jog tomorrow?'),
            _FakeMessage(
                'Skip the jog tomorrow morning.',
                response_metadata={'model_name': 'fake-model', 'finish_reason': 'stop', 'id': 'resp_fake'},
                usage_metadata={'input_tokens': 12, 'output_tokens': 6, 'total_tokens': 18},
            ),
        ]
    }

    monkeypatch.setattr(AgentLensLangGraphAgent, '_build_agent', lambda self: _FakeAgent(fake_result))

    agent = AgentLensLangGraphAgent(
        client=client,
        model=object(),
        tools=[],
        system_prompt='Be concise.',
        agent_name='fake_langgraph_agent',
    )
    result = agent.invoke('Should I jog tomorrow morning?')

    assert result['final_answer'] == 'Skip the jog tomorrow morning.'
    records = [json.loads(line) for line in next(storage.glob('*.jsonl')).read_text(encoding='utf-8').splitlines() if line.strip()]
    assert records[0]['type'] == 'run.start'
    assert records[-1]['type'] == 'run.end'
    assert records[-1]['payload']['final_answer'] == 'Skip the jog tomorrow morning.'
