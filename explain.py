from __future__ import annotations

from typing import Any, Dict, List


def build_counterfactual_hints(summary: Dict[str, Any]) -> List[str]:
    hints: List[str] = []
    tool_evidence = summary.get('tool_evidence', [])
    turns = summary.get('turns', [])
    answer_alignment = summary.get('answer_alignment', {})
    suspicious = summary.get('suspicious_signals', [])
    final_answer = summary.get('final_answer')

    if tool_evidence:
        first_tool = tool_evidence[0]
        hints.append(
            f"If `{first_tool.get('tool_name')}` returned the opposite outcome, the final answer should be re-checked first."
        )

    if turns:
        first_tool_turn = next((turn for turn in turns if turn.get('tool_calls')), turns[0])
        hints.append(
            f"Rerun turn {first_tool_turn.get('turn_index')} first, because that is where the model committed to a tool-use path."
        )

    alignment_status = answer_alignment.get('status')
    if alignment_status == 'aligned':
        hints.append('The current answer appears grounded in tool evidence, so regressions are most likely to come from changed tool outputs or retrieval inputs.')
    elif alignment_status in {'unclear', 'needs_review'}:
        hints.append('The answer/evidence link is weak, so try replaying the final model turn with stricter instructions to use tool results explicitly.')
    elif alignment_status == 'no_tool_evidence':
        hints.append('Add at least one external evidence source or tool call before trusting this answer in production.')

    if suspicious:
        first_signal = suspicious[0]
        hints.append(
            f"If you only inspect one branch, inspect the trajectory around event #{first_signal.get('event_index')} where `{first_signal.get('type')}` first appeared."
        )
    elif final_answer:
        hints.append('No explicit failure signal was emitted, so the most useful counterfactual is: what would the answer become if the strongest tool result changed?')

    return hints[:4]


def build_debug_story(summary: Dict[str, Any]) -> List[str]:
    runtime = summary.get('runtime') or 'unknown runtime'
    agent_name = summary.get('agent_name') or 'unknown agent'
    turns = summary.get('turns', [])
    tool_evidence = summary.get('tool_evidence', [])
    answer_alignment = summary.get('answer_alignment', {})
    final_answer = summary.get('final_answer')
    suspicious = summary.get('suspicious_signals', [])

    story = [
        f"This run used {runtime} with agent `{agent_name}` and recorded {len(turns)} model turn(s)."
    ]

    if turns:
        first_turn = turns[0]
        tool_calls = first_turn.get('tool_calls', [])
        if tool_calls:
            tool_names = ', '.join(call.get('tool_name', 'unknown_tool') for call in tool_calls)
            story.append(f"The first meaningful model action was to call tool(s): {tool_names}.")

    if tool_evidence:
        first_tool = tool_evidence[0]
        story.append(
            f"Fresh tool evidence came from `{first_tool.get('tool_name')}`: {first_tool.get('content')}."
        )

    if final_answer:
        story.append(f"The final answer was: {final_answer}")

    alignment_status = answer_alignment.get('status')
    alignment_reason = answer_alignment.get('reason')
    if alignment_status:
        story.append(f"Answer grounding check: {alignment_status}. {alignment_reason}")

    if suspicious:
        first_signal = suspicious[0]
        story.append(
            f"The first suspicious signal was `{first_signal.get('type')}` at event #{first_signal.get('event_index')}."
        )
    else:
        story.append('No explicit suspicious signal was emitted, so the main review question is whether the final answer stayed grounded in the freshest evidence.')

    return story


def build_failure_card(summary: Dict[str, Any]) -> Dict[str, Any]:
    suspicious = summary.get('suspicious_signals', [])
    likely_failure = summary.get('likely_failure_point')
    memory_influence = summary.get('memory_influence', [])
    failure_chain = summary.get('failure_chain', [])
    evidence_summary = summary.get('evidence_summary', [])

    root_cause = 'No explicit root cause identified yet.'
    evidence: List[str] = []
    inspect_next: List[str] = []

    if suspicious:
        first = suspicious[0]
        failure_mode = summary.get('failure_mode', 'unknown_failure_mode')
        answer_risk = summary.get('answer_risk', 'unknown')
        confidence = summary.get('confidence', 'low')
        root_cause = f"Likely root cause: {first.get('type')} ({failure_mode}, risk={answer_risk}, confidence={confidence})"
        evidence.append(first.get('reason', 'Suspicious signal emitted'))

    if likely_failure:
        evidence.append(f"Likely failure point at event index {likely_failure.get('event_index')}")

    recall_items = [m for m in memory_influence if m.get('kind') == 'recall']
    if recall_items:
        evidence.append(f"{len(recall_items)} memory recall event(s) influenced the run")
        inspect_next.append('Check whether recalled memory was stale or weakly relevant')

    if evidence_summary:
        evidence.extend(evidence_summary[:3])

    if failure_chain:
        inspect_next.append('Walk the failure chain from the first suspicious step to the final answer')

    if summary.get('tool_sequence'):
        inspect_next.append('Inspect tool outputs around the divergence/failure step')

    if not inspect_next:
        inspect_next.append('Inspect the earliest non-trivial decision in the run')

    return {
        'root_cause': root_cause,
        'evidence': evidence,
        'inspect_next': inspect_next,
        'debug_story': build_debug_story(summary),
        'counterfactual_hints': build_counterfactual_hints(summary),
    }
