from __future__ import annotations

from typing import Any, Dict, List, Optional


ERROR_TYPES = {
    'memory_conflict',
    'stale_memory_override',
    'span_error',
    'llm_error',
    'used_wrong_tool',
    'used_wrong_tool_argument',
    'tool_result_ignored',
    'goal_partially_completed',
    'clarification_missing',
}

WEATHER_KEYWORDS = {
    'rain',
    'rainy',
    'sunny',
    'cloudy',
    'storm',
    'stormy',
    'snow',
    'snowy',
    'indoor',
    'treadmill',
    'outdoor',
}


def _tool_result_by_call_span(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for event in events:
        if event.get('type') == 'tool.result':
            parent = event.get('parent_span_id')
            if parent:
                mapping[parent] = event
    return mapping


def _extract_answer_risk(final_answer: Optional[str], suspicious_signals: List[Dict[str, Any]]) -> str:
    if not final_answer and suspicious_signals:
        return 'failed_before_final_answer'
    if not suspicious_signals:
        return 'no_explicit_risk_found'

    answer = (final_answer or '').lower()
    if any(keyword in answer for keyword in ['skip', 'not', 'avoid', 'cannot', 'error', 'failed']):
        return 'visible_failure'
    return 'hidden_degradation'


def _extract_keywords(value: Any) -> set[str]:
    text = str(value or '').lower()
    return {keyword for keyword in WEATHER_KEYWORDS if keyword in text}


def _summarize_answer_alignment(final_answer: Optional[str], tool_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not final_answer:
        return {
            'status': 'no_final_answer',
            'reason': 'No final answer was recorded for this run.',
            'matching_terms': [],
            'tool_terms': [],
            'answer_terms': [],
        }

    if not tool_evidence:
        return {
            'status': 'no_tool_evidence',
            'reason': 'No tool evidence was captured, so answer grounding cannot be checked.',
            'matching_terms': [],
            'tool_terms': [],
            'answer_terms': sorted(_extract_keywords(final_answer)),
        }

    tool_terms = set()
    for item in tool_evidence:
        tool_terms.update(_extract_keywords(item.get('content')))
    answer_terms = _extract_keywords(final_answer)
    matching = sorted(tool_terms & answer_terms)

    if matching:
        return {
            'status': 'aligned',
            'reason': f"Final answer echoes tool evidence terms: {', '.join(matching)}.",
            'matching_terms': matching,
            'tool_terms': sorted(tool_terms),
            'answer_terms': sorted(answer_terms),
        }

    answer_text = str(final_answer or '').lower()
    if tool_terms & {'rain', 'rainy', 'storm', 'stormy', 'snow', 'snowy'}:
        if any(keyword in answer_text for keyword in ['skip', 'indoor', 'treadmill', 'not ideal', 'avoid']):
            return {
                'status': 'aligned',
                'reason': 'Tool evidence suggests poor outdoor conditions and the final answer recommends caution.',
                'matching_terms': [],
                'tool_terms': sorted(tool_terms),
                'answer_terms': sorted(answer_terms),
            }

    if tool_terms & {'sunny', 'cloudy'}:
        if any(keyword in answer_text for keyword in ['jog', 'fine', 'outdoor', 'go ahead']):
            return {
                'status': 'aligned',
                'reason': 'Tool evidence suggests acceptable outdoor conditions and the final answer stays permissive.',
                'matching_terms': [],
                'tool_terms': sorted(tool_terms),
                'answer_terms': sorted(answer_terms),
            }

    if tool_terms and answer_terms:
        return {
            'status': 'unclear',
            'reason': 'Tool evidence and final answer both contain domain signals, but they do not clearly overlap.',
            'matching_terms': [],
            'tool_terms': sorted(tool_terms),
            'answer_terms': sorted(answer_terms),
        }

    return {
        'status': 'needs_review',
        'reason': 'Tool evidence exists, but there is not enough structured overlap to judge answer grounding automatically.',
        'matching_terms': [],
        'tool_terms': sorted(tool_terms),
        'answer_terms': sorted(answer_terms),
    }


def _compute_debug_priority(summary: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []

    suspicious = summary.get('suspicious_signals', [])
    if suspicious:
        score += 45
        reasons.append('Suspicious signals were emitted during the run.')

    answer_risk = summary.get('answer_risk')
    if answer_risk == 'visible_failure':
        score += 30
        reasons.append('The final answer looks visibly degraded.')
    elif answer_risk == 'hidden_degradation':
        score += 20
        reasons.append('The run may be degraded even though the final answer still looks plausible.')

    alignment = (summary.get('answer_alignment') or {}).get('status')
    if alignment in {'unclear', 'needs_review'}:
        score += 20
        reasons.append('Answer grounding against tool evidence is weak or unclear.')
    elif alignment == 'no_tool_evidence':
        score += 10
        reasons.append('No external evidence was captured, so confidence should stay low.')

    turn_count = len(summary.get('turns', []))
    if turn_count >= 3:
        score += 10
        reasons.append('The run spans multiple model turns, so debugging cost is higher.')

    if summary.get('memory_influence'):
        score += 5
        reasons.append('Memory influenced the run, which increases the chance of hidden failure modes.')

    score = min(score, 100)
    if score >= 70:
        level = 'high'
    elif score >= 35:
        level = 'medium'
    else:
        level = 'low'

    if not reasons:
        reasons.append('No strong failure signals were detected, so this run is lower priority for manual review.')

    return {
        'score': score,
        'level': level,
        'reasons': reasons[:4],
    }


def _build_failure_fingerprint(summary: Dict[str, Any]) -> Dict[str, Any]:
    suspicious = summary.get('suspicious_signals', [])
    answer_alignment = summary.get('answer_alignment', {})
    tool_evidence = summary.get('tool_evidence', [])
    memory_influence = summary.get('memory_influence', [])
    turns = summary.get('turns', [])

    tokens: List[str] = []
    label = summary.get('failure_mode') or 'unknown_failure'

    if suspicious:
        signal_type = suspicious[0].get('type') or 'unknown_signal'
        tokens.append(signal_type)
    else:
        signal_type = 'no_explicit_signal'
        tokens.append(signal_type)

    tokens.append('memory_involved' if memory_influence else 'memory_not_used')
    tokens.append('tool_evidence_present' if tool_evidence else 'tool_evidence_missing')

    alignment_status = answer_alignment.get('status') or 'unknown_alignment'
    tokens.append(alignment_status)

    if len(turns) >= 3:
        tokens.append('multi_turn')
    elif turns:
        tokens.append('single_turn')
    else:
        tokens.append('no_turns')

    answer_risk = summary.get('answer_risk') or 'unknown_risk'
    tokens.append(answer_risk)

    if signal_type == 'memory_conflict':
        label = 'memory-vs-tool-conflict'
    elif signal_type == 'stale_memory_override':
        label = 'stale-memory-override'
    elif signal_type == 'span_error':
        label = 'runtime-span-error'
    elif signal_type == 'used_wrong_tool':
        label = 'wrong-tool-selected'
    elif signal_type == 'used_wrong_tool_argument':
        label = 'wrong-tool-argument'
    elif signal_type == 'tool_result_ignored':
        label = 'tool-result-ignored'
    elif signal_type == 'goal_partially_completed':
        label = 'goal-partially-completed'
    elif signal_type == 'clarification_missing':
        label = 'clarification-missing'
    elif alignment_status in {'unclear', 'needs_review'} and tool_evidence:
        label = 'answer-ungrounded-with-tools'
    elif alignment_status == 'no_tool_evidence':
        label = 'answer-without-external-evidence'
    elif summary.get('failure_mode') == 'no_explicit_failure':
        label = 'no-explicit-failure'

    fingerprint_id = '|'.join(tokens)
    return {
        'id': fingerprint_id,
        'label': label,
        'tokens': tokens,
    }


def summarize_run(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        'final_answer': None,
        'likely_failure_point': None,
        'memory_influence': [],
        'tool_sequence': [],
        'tool_evidence': [],
        'model_turns': [],
        'turns': [],
        'suspicious_signals': [],
        'notes': [],
        'failure_mode': 'no_explicit_failure',
        'failure_chain': [],
        'confidence': 'low',
        'evidence_summary': [],
        'runtime': 'unknown',
        'agent_name': None,
        'answer_alignment': {},
        'debug_priority': {},
    }

    latest_recall: Optional[Dict[str, Any]] = None
    latest_tool_result: Optional[Dict[str, Any]] = None
    latest_decision: Optional[Dict[str, Any]] = None
    tool_calls_by_id: Dict[str, Dict[str, Any]] = {}
    current_turn: Optional[Dict[str, Any]] = None

    def ensure_turn() -> Dict[str, Any]:
        nonlocal current_turn
        if current_turn is None:
            current_turn = {
                'turn_index': len(summary['turns']) + 1,
                'request_event_index': None,
                'model': None,
                'prompt': None,
                'messages': [],
                'tool_calls': [],
                'tool_results': [],
                'response': None,
            }
            summary['turns'].append(current_turn)
        return current_turn

    for idx, e in enumerate(events):
        et = e.get('type')
        payload = e.get('payload') or {}

        if et == 'run.start':
            summary['runtime'] = payload.get('runtime', summary['runtime'])
            summary['agent_name'] = payload.get('agent_name', summary['agent_name'])

        if et == 'llm.request':
            current_turn = {
                'turn_index': len(summary['turns']) + 1,
                'request_event_index': idx,
                'model': payload.get('model'),
                'prompt': payload.get('prompt'),
                'messages': payload.get('messages', []),
                'tool_calls': [],
                'tool_results': [],
                'response': None,
            }
            summary['turns'].append(current_turn)

        if et == 'agent.decision':
            latest_decision = {
                'event_index': idx,
                'name': payload.get('name'),
                'payload': payload,
            }
            summary['model_turns'].append({
                'event_index': idx,
                'kind': 'agent_decision',
                'summary': payload.get('name') or 'agent decision',
            })

        if et == 'tool.call':
            turn = ensure_turn()
            tool_name = payload.get('tool_name')
            tool_call_id = payload.get('tool_call_id')
            if tool_name:
                summary['tool_sequence'].append(tool_name)
                summary['failure_chain'].append({
                    'event_index': idx,
                    'kind': 'tool_call',
                    'label': f'tool call: {tool_name}',
                })
                if tool_call_id:
                    tool_calls_by_id[tool_call_id] = {
                        'tool_name': tool_name,
                        'args': payload.get('args', {}),
                        'event_index': idx,
                    }
                if turn is not None:
                    turn['tool_calls'].append({
                        'event_index': idx,
                        'tool_name': tool_name,
                        'args': payload.get('args', {}),
                        'tool_call_id': tool_call_id,
                    })

        if et == 'tool.result':
            turn = ensure_turn()
            latest_tool_result = {
                'event_index': idx,
                'payload': payload,
            }
            tool_call_id = payload.get('tool_call_id')
            tool_name = tool_calls_by_id.get(tool_call_id, {}).get('tool_name')
            result_content = payload.get('content') or payload
            summary['tool_evidence'].append({
                'event_index': idx,
                'tool_name': tool_name or 'unknown_tool',
                'content': result_content,
            })
            if turn is not None:
                turn['tool_results'].append({
                    'event_index': idx,
                    'tool_name': tool_name or 'unknown_tool',
                    'content': result_content,
                    'tool_call_id': tool_call_id,
                })

        if et == 'memory.write':
            content = payload.get('content')
            if content:
                item = {
                    'kind': 'write',
                    'content': content,
                    'event_index': idx,
                }
                summary['memory_influence'].append(item)
                summary['failure_chain'].append({
                    'event_index': idx,
                    'kind': 'memory_write',
                    'label': f'memory write: {content}',
                })

        if et == 'memory.recall':
            content = payload.get('content')
            if content:
                latest_recall = {
                    'kind': 'recall',
                    'content': content,
                    'event_index': idx,
                    'reason': payload.get('reason'),
                }
                summary['memory_influence'].append(latest_recall)
                summary['failure_chain'].append({
                    'event_index': idx,
                    'kind': 'memory_recall',
                    'label': f'memory recall: {content}',
                })

        if et == 'llm.response':
            turn = ensure_turn()
            response_text = payload.get('response')
            tool_calls = payload.get('tool_calls') or []
            turn_summary = response_text or payload.get('decision') or 'llm response'
            summary['model_turns'].append({
                'event_index': idx,
                'kind': 'llm_response',
                'summary': turn_summary,
                'tool_calls': tool_calls,
            })
            if tool_calls:
                tool_names = ', '.join(call.get('name', 'unknown_tool') for call in tool_calls)
                summary['failure_chain'].append({
                    'event_index': idx,
                    'kind': 'model_tool_choice',
                    'label': f'model selected tool(s): {tool_names}',
                })
            if turn is not None:
                turn['response_event_index'] = idx
                turn['response'] = response_text
                turn['tool_calls'].extend([
                    {
                        'event_index': idx,
                        'tool_name': call.get('name', 'unknown_tool'),
                        'args': call.get('args', {}),
                        'tool_call_id': call.get('id'),
                        'source': 'model_response',
                    }
                    for call in tool_calls
                ])
                response_metadata = {
                    key: payload.get(key)
                    for key in ('finish_reason', 'response_id', 'response_model', 'decision')
                    if payload.get(key) is not None
                }
                if response_metadata:
                    turn['response_metadata'] = response_metadata

        if et == 'error':
            reason = payload.get('message') or 'error event emitted'
            signal_type = payload.get('kind') or 'error'
            signal = {
                'event_index': idx,
                'type': signal_type,
                'reason': reason,
            }
            summary['suspicious_signals'].append(signal)
            summary['failure_chain'].append({
                'event_index': idx,
                'kind': 'error',
                'label': f'{signal_type}: {reason}',
            })
            if summary['likely_failure_point'] is None:
                summary['likely_failure_point'] = {
                    'event_index': idx,
                    'type': 'error',
                    'reason': reason,
                }

        if et == 'run.end':
            summary['final_answer'] = payload.get('final_answer')
            summary['failure_chain'].append({
                'event_index': idx,
                'kind': 'final_answer',
                'label': f"final answer: {payload.get('final_answer')}",
            })

    if summary['suspicious_signals']:
        first_signal = summary['suspicious_signals'][0]
        summary['confidence'] = 'high' if first_signal['type'] in ERROR_TYPES else 'medium'

        if first_signal['type'] == 'memory_conflict':
            summary['failure_mode'] = 'memory_vs_tool_conflict'
        elif first_signal['type'] == 'stale_memory_override':
            summary['failure_mode'] = 'stale_memory_override'
        elif first_signal['type'] == 'used_wrong_tool':
            summary['failure_mode'] = 'wrong_tool_selected'
        elif first_signal['type'] == 'used_wrong_tool_argument':
            summary['failure_mode'] = 'wrong_tool_argument'
        elif first_signal['type'] == 'tool_result_ignored':
            summary['failure_mode'] = 'tool_result_ignored'
        elif first_signal['type'] == 'goal_partially_completed':
            summary['failure_mode'] = 'goal_partially_completed'
        elif first_signal['type'] == 'clarification_missing':
            summary['failure_mode'] = 'clarification_failure'
        elif first_signal['type'] == 'llm_error':
            summary['failure_mode'] = 'llm_runtime_error'
        else:
            summary['failure_mode'] = 'runtime_error'

        if latest_recall:
            summary['evidence_summary'].append(
                f"memory recall at event {latest_recall['event_index']}: {latest_recall['content']}"
            )
        if latest_tool_result:
            summary['evidence_summary'].append(
                f"tool result at event {latest_tool_result['event_index']}: {latest_tool_result['payload']}"
            )
        if latest_decision:
            summary['evidence_summary'].append(
                f"decision span at event {latest_decision['event_index']}: {latest_decision['name']}"
            )
        summary['evidence_summary'].append(
            f"first suspicious signal at event {first_signal['event_index']}: {first_signal['type']}"
        )
    else:
        recall_events = [m for m in summary['memory_influence'] if m['kind'] == 'recall']
        if recall_events:
            summary['notes'].append('Memory recall occurred; verify whether recalled memory was relevant.')
        if summary['runtime'] == 'langgraph':
            summary['notes'].append('Inspect model/tool handoff across LangGraph turns to see where reasoning changed.')
        if summary['tool_evidence']:
            first_tool = summary['tool_evidence'][0]
            summary['notes'].append(
                f"Fresh tool evidence from {first_tool['tool_name']} is available; compare it against the final answer."
            )
        if summary['tool_sequence']:
            summary['notes'].append('Inspect tool outputs if final answer quality looks wrong.')
        if not summary['notes']:
            summary['notes'].append('No explicit failure signal found; inspect decision quality manually.')

    summary['answer_risk'] = _extract_answer_risk(summary['final_answer'], summary['suspicious_signals'])
    summary['answer_alignment'] = _summarize_answer_alignment(summary['final_answer'], summary['tool_evidence'])
    summary['debug_priority'] = _compute_debug_priority(summary)
    summary['failure_fingerprint'] = _build_failure_fingerprint(summary)
    return summary


def summarize_divergence(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Dict[str, Any]:
    max_len = min(len(a), len(b))
    divergence = None
    timeline: List[Dict[str, Any]] = []
    differing_steps = 0

    for i in range(max_len):
        ea, eb = a[i], b[i]
        a_payload = ea.get('payload') or {}
        b_payload = eb.get('payload') or {}
        same = ea.get('type') == eb.get('type') and a_payload == b_payload
        if not same:
            differing_steps += 1
            step = {
                'event_index': i,
                'a_type': ea.get('type'),
                'b_type': eb.get('type'),
                'a_payload': a_payload,
                'b_payload': b_payload,
                'difference_kind': 'type_mismatch' if ea.get('type') != eb.get('type') else 'payload_mismatch',
            }
            timeline.append(step)
            if divergence is None:
                divergence = step

    if len(a) != len(b):
        differing_steps += abs(len(a) - len(b))
        step = {
            'event_index': max_len,
            'a_type': a[max_len].get('type') if len(a) > max_len else None,
            'b_type': b[max_len].get('type') if len(b) > max_len else None,
            'a_payload': a[max_len].get('payload') if len(a) > max_len else {},
            'b_payload': b[max_len].get('payload') if len(b) > max_len else {},
            'difference_kind': 'length_mismatch',
        }
        timeline.append(step)
        if divergence is None:
            divergence = step

    a_summary = summarize_run(a)
    b_summary = summarize_run(b)

    severity = 'none'
    if divergence is not None:
        if a_summary.get('final_answer') != b_summary.get('final_answer'):
            severity = 'high'
        elif b_summary.get('suspicious_signals') and not a_summary.get('suspicious_signals'):
            severity = 'high'
        elif differing_steps >= 2:
            severity = 'medium'
        else:
            severity = 'low'

    return {
        'first_divergence': divergence,
        'divergence_timeline': timeline,
        'divergence_count': differing_steps,
        'severity': severity,
        'a_final_answer': a_summary.get('final_answer'),
        'b_final_answer': b_summary.get('final_answer'),
        'a_suspicious_signals': a_summary.get('suspicious_signals', []),
        'b_suspicious_signals': b_summary.get('suspicious_signals', []),
        'a_answer_risk': a_summary.get('answer_risk'),
        'b_answer_risk': b_summary.get('answer_risk'),
    }
