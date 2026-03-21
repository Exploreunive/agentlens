from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .client import AgentLensClient


class OpenAIResponsesTracer:
    """A tiny local-first wrapper for instrumenting OpenAI-compatible calls.

    The wrapped callable should return a dict-like object with optional keys such as:
    - output_text / content / response
    - usage: {input_tokens, output_tokens, total_tokens}
    - finish_reason
    """

    def __init__(self, client: AgentLensClient):
        self.client = client

    def trace_chat_completion(
        self,
        *,
        run_id: str,
        model: str,
        prompt: str,
        call: Callable[[], Dict[str, Any]],
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        llm_events = self.client.record_llm_call(
            run_id=run_id,
            model=model,
            prompt=prompt,
            parent_span_id=parent_span_id,
        )
        try:
            response = call()
        except Exception as exc:
            self.client.emit(
                type='error',
                run_id=run_id,
                payload={
                    'kind': 'llm_error',
                    'message': str(exc),
                    'model': model,
                },
                status='error',
                parent_span_id=llm_events['request'].span_id,
            )
            raise

        usage = response.get('usage') or {}
        output_text = response.get('output_text') or response.get('content') or response.get('response')
        finish_reason = response.get('finish_reason')
        self.client.emit(
            type='llm.response',
            run_id=run_id,
            payload={
                'response': output_text,
                'finish_reason': finish_reason,
            },
            metrics={
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
            },
            parent_span_id=llm_events['request'].span_id,
        )
        return response
