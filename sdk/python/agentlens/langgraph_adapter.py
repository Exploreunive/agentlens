from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Sequence

from .client import AgentLensClient


def _stringify_content(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get('text') or item.get('content') or repr(item)
                parts.append(str(text))
            else:
                parts.append(str(item))
        return '\n'.join(part for part in parts if part)
    return str(value)


def _extract_message_text(message: Any) -> str:
    return _stringify_content(getattr(message, 'content', None))


def _extract_model_name(model: Any) -> str:
    return (
        getattr(model, 'model_name', None)
        or getattr(model, 'model', None)
        or model.__class__.__name__
    )


def _serialize_messages(messages: Iterable[Any]) -> list[dict[str, Any]]:
    serialized = []
    for message in messages:
        serialized.append(
            {
                'type': message.__class__.__name__,
                'content': _extract_message_text(message),
            }
        )
    return serialized


def _extract_usage_metrics(message: Any) -> Dict[str, int]:
    usage = getattr(message, 'usage_metadata', None) or {}
    response_metadata = getattr(message, 'response_metadata', None) or {}
    token_usage = response_metadata.get('token_usage') or {}
    return {
        'input_tokens': int(usage.get('input_tokens', token_usage.get('prompt_tokens', 0)) or 0),
        'output_tokens': int(usage.get('output_tokens', token_usage.get('completion_tokens', 0)) or 0),
        'total_tokens': int(usage.get('total_tokens', token_usage.get('total_tokens', 0)) or 0),
    }


def _extract_final_answer(result: Any) -> Optional[str]:
    if isinstance(result, dict):
        messages = result.get('messages') or []
        for message in reversed(messages):
            text = _extract_message_text(message)
            if text:
                return text
    return None


@dataclass
class _RunContext:
    run_id: str
    root_span_id: str


class AgentLensLangGraphAgent:
    def __init__(
        self,
        *,
        client: AgentLensClient,
        model: Any,
        tools: Sequence[Callable[..., Any] | Any],
        system_prompt: Optional[str] = None,
        agent_name: str = 'langgraph_agent',
    ):
        self.client = client
        self.model = model
        self.tools = list(tools)
        self.system_prompt = system_prompt
        self.agent_name = agent_name
        self._active_run: Optional[_RunContext] = None
        self.agent = self._build_agent()

    def _build_agent(self) -> Any:
        try:
            from langchain.agents import create_agent
            from langchain.agents.middleware import wrap_model_call, wrap_tool_call
        except ImportError as exc:
            raise ImportError(
                'LangGraph adapter requires langchain, langgraph, and langchain-openai. '
                'Install them with `pip install ".[langgraph]"`.'
            ) from exc

        @wrap_model_call
        def trace_model(request: Any, handler: Any) -> Any:
            run = self._require_active_run()
            prompt = _stringify_content(
                '\n'.join(
                    filter(
                        None,
                        (_extract_message_text(message) for message in request.messages),
                    )
                )
            )
            llm_request = self.client.emit(
                type='llm.request',
                run_id=run.run_id,
                payload={
                    'model': _extract_model_name(request.model),
                    'prompt': prompt,
                    'messages': _serialize_messages(request.messages),
                    'tool_count': len(request.tools or []),
                },
                parent_span_id=run.root_span_id,
            )

            try:
                response = handler(request)
            except Exception as exc:
                self.client.emit(
                    type='error',
                    run_id=run.run_id,
                    payload={
                        'kind': 'llm_error',
                        'message': str(exc),
                        'model': _extract_model_name(request.model),
                    },
                    status='error',
                    parent_span_id=llm_request.span_id,
                )
                raise

            message = response.result[-1] if getattr(response, 'result', None) else None
            payload: Dict[str, Any] = {
                'response': _extract_message_text(message) if message is not None else '',
            }
            if message is not None:
                tool_calls = getattr(message, 'tool_calls', None) or []
                if tool_calls:
                    payload['tool_calls'] = [
                        {
                            'name': call.get('name'),
                            'id': call.get('id'),
                            'args': call.get('args'),
                        }
                        for call in tool_calls
                    ]
                    payload['decision'] = f"tool_calls={','.join(call.get('name', 'unknown') for call in tool_calls)}"

                response_metadata = getattr(message, 'response_metadata', None) or {}
                if response_metadata.get('finish_reason') is not None:
                    payload['finish_reason'] = response_metadata.get('finish_reason')
                if response_metadata.get('id') is not None:
                    payload['response_id'] = response_metadata.get('id')
                if response_metadata.get('model_name') is not None:
                    payload['response_model'] = response_metadata.get('model_name')

            self.client.emit(
                type='llm.response',
                run_id=run.run_id,
                payload=payload,
                metrics=_extract_usage_metrics(message),
                parent_span_id=llm_request.span_id,
            )
            return response

        @wrap_tool_call
        def trace_tool(request: Any, handler: Any) -> Any:
            run = self._require_active_run()
            tool_call = request.tool_call or {}
            call_event = self.client.emit(
                type='tool.call',
                run_id=run.run_id,
                payload={
                    'tool_name': tool_call.get('name'),
                    'args': tool_call.get('args', {}),
                    'tool_call_id': tool_call.get('id'),
                },
                parent_span_id=run.root_span_id,
            )
            try:
                result = handler(request)
            except Exception as exc:
                self.client.emit(
                    type='error',
                    run_id=run.run_id,
                    payload={
                        'kind': 'tool_error',
                        'message': str(exc),
                        'tool_name': tool_call.get('name'),
                    },
                    status='error',
                    parent_span_id=call_event.span_id,
                )
                raise

            self.client.emit(
                type='tool.result',
                run_id=run.run_id,
                payload={
                    'content': _stringify_content(getattr(result, 'content', result)),
                    'tool_call_id': tool_call.get('id'),
                },
                parent_span_id=call_event.span_id,
            )
            return result

        return create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=[trace_model, trace_tool],
            name=self.agent_name,
        )

    def _require_active_run(self) -> _RunContext:
        if self._active_run is None:
            raise RuntimeError('No active AgentLens run context is set')
        return self._active_run

    def invoke(self, user_input: str, *, run_id: Optional[str] = None) -> Dict[str, Any]:
        run_id = run_id or self.client.new_run()
        self.client.emit(
            type='run.start',
            run_id=run_id,
            payload={
                'task': user_input,
                'runtime': 'langgraph',
                'agent_name': self.agent_name,
            },
        )

        with self.client.span(
            run_id=run_id,
            name=self.agent_name,
            payload={'runtime': 'langgraph'},
        ) as root_span:
            self._active_run = _RunContext(run_id=run_id, root_span_id=root_span.span_id)
            try:
                result = self.agent.invoke(
                    {'messages': [{'role': 'user', 'content': user_input}]}
                )
            finally:
                self._active_run = None

        final_answer = _extract_final_answer(result)
        self.client.emit(
            type='run.end',
            run_id=run_id,
            payload={'final_answer': final_answer},
        )
        return {'run_id': run_id, 'result': result, 'final_answer': final_answer}


def build_chat_openai_model(
    *,
    model: str,
    api_key: str,
    base_url: Optional[str] = None,
    temperature: float = 0,
    **kwargs: Any,
) -> Any:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise ImportError(
            'ChatOpenAI helper requires langchain-openai. Install it with `pip install ".[langgraph]"`.'
        ) from exc

    init_kwargs = {
        'model': model,
        'api_key': api_key,
        'temperature': temperature,
        **kwargs,
    }
    if base_url:
        init_kwargs['base_url'] = base_url
    return ChatOpenAI(**init_kwargs)
