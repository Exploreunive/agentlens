from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sdk' / 'python'))

from agentlens import AgentLensClient
from agentlens import AgentLensLangGraphAgent, build_chat_openai_model


def weather_snapshot(city: str) -> str:
    """Get a lightweight weather snapshot for a city."""
    return f'{city}: rain'


def main() -> None:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('Set OPENAI_API_KEY to run the LangGraph demo.')

    client = AgentLensClient(redact_sensitive=True)
    model = build_chat_openai_model(
        model=os.getenv('AGENTLENS_OPENAI_MODEL', 'gpt-5.2'),
        api_key=api_key,
        base_url=os.getenv('OPENAI_BASE_URL'),
    )
    agent = AgentLensLangGraphAgent(
        client=client,
        model=model,
        tools=[weather_snapshot],
        system_prompt='Use tools when they provide fresher evidence than assumptions. Keep the answer concise.',
        agent_name='langgraph_weather_agent',
    )
    result = agent.invoke('Should I jog tomorrow morning in Shanghai? Use the weather tool before answering.')
    print(f"Generated LangGraph demo run: {result['run_id']}")
    print(result['final_answer'])


if __name__ == '__main__':
    main()
