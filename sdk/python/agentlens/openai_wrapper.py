from __future__ import annotations

from time import perf_counter
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

    def _lookup(self, value: Any, field: str, default: Any = None) -> Any:
        if isinstance(value, dict):
            return value.get(field, default)
        return getattr(value, field, default)

    def _extract_output_text(self, response: Any) -> Optional[str]:
        direct_text = self._lookup(response, 'output_text')
        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text

        for field in ('content', 'response'):
            text = self._lookup(response, field)
            if isinstance(text, str) and text.strip():
                return text

        output_items = self._lookup(response, 'output', [])
        for item in output_items or []:
            item_type = self._lookup(item, 'type')
            if item_type == 'message':
                for content in self._lookup(item, 'content', []) or []:
                    if self._lookup(content, 'type') in {'output_text', 'text'}:
                        text = self._lookup(content, 'text')
                        if isinstance(text, str) and text.strip():
                            return text

        choices = self._lookup(response, 'choices', [])
        for choice in choices or []:
            message = self._lookup(choice, 'message')
            text = self._lookup(message, 'content')
            if isinstance(text, str) and text.strip():
                return text

        return None

    def _normalize_usage(self, response: Any) -> Dict[str, int]:
        usage = self._lookup(response, 'usage', {}) or {}
        return {
            'input_tokens': int(self._lookup(usage, 'input_tokens', self._lookup(usage, 'prompt_tokens', 0)) or 0),
            'output_tokens': int(self._lookup(usage, 'output_tokens', self._lookup(usage, 'completion_tokens', 0)) or 0),
            'total_tokens': int(self._lookup(usage, 'total_tokens', 0) or 0),
        }

    def _normalize_response_payload(self, response: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        response_id = self._lookup(response, 'id')
        if response_id is not None:
            payload['response_id'] = response_id

        model = self._lookup(response, 'model')
        if model is not None:
            payload['response_model'] = model

        finish_reason = self._lookup(response, 'finish_reason')
        if finish_reason is None:
            choices = self._lookup(response, 'choices', [])
            if choices:
                finish_reason = self._lookup(choices[0], 'finish_reason')
        if finish_reason is not None:
            payload['finish_reason'] = finish_reason

        output_text = self._extract_output_text(response)
        if output_text is not None:
            payload['response'] = output_text

        return payload

    def _emit_llm_success(
        self,
        *,
        run_id: str,
        request_span_id: str,
        response: Any,
        latency_ms: int,
    ) -> None:
        payload = self._normalize_response_payload(response)
        metrics = self._normalize_usage(response)
        metrics['latency_ms'] = latency_ms
        self.client.emit(
            type='llm.response',
            run_id=run_id,
            payload=payload,
            metrics=metrics,
            parent_span_id=request_span_id,
        )

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
            emit_response=False,
        )
        started = perf_counter()
        try:
            response = call()
        except Exception as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            self.client.emit(
                type='error',
                run_id=run_id,
                payload={
                    'kind': 'llm_error',
                    'message': str(exc),
                    'model': model,
                },
                status='error',
                metrics={'latency_ms': latency_ms},
                parent_span_id=llm_events['request'].span_id,
            )
            raise

        latency_ms = int((perf_counter() - started) * 1000)
        self._emit_llm_success(
            run_id=run_id,
            request_span_id=llm_events['request'].span_id,
            response=response,
            latency_ms=latency_ms,
        )
        return response

    def trace_responses_create(
        self,
        *,
        run_id: str,
        client: Any,
        model: str,
        input: Any,
        parent_span_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        def call() -> Any:
            return client.responses.create(model=model, input=input, **kwargs)

        prompt = input if isinstance(input, str) else repr(input)
        return self.trace_chat_completion(
            run_id=run_id,
            model=model,
            prompt=prompt,
            call=call,
            parent_span_id=parent_span_id,
        )

    def trace_chat_completions_create(
        self,
        *,
        run_id: str,
        client: Any,
        model: str,
        messages: Any,
        parent_span_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        def call() -> Any:
            return client.chat.completions.create(model=model, messages=messages, **kwargs)

        prompt = repr(messages)
        return self.trace_chat_completion(
            run_id=run_id,
            model=model,
            prompt=prompt,
            call=call,
            parent_span_id=parent_span_id,
        )
