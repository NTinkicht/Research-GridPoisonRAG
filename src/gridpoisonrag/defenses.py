from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .grading import parse_committed_value
from .prompts import rag_messages


@dataclass(frozen=True)
class DefenseDecision:
    answer: str
    flagged: bool
    reason: str


def isolate_then_aggregate(client, query: str, passages: list[str], unit: str) -> str:
    values: list[float] = []
    for passage in passages:
        text = client.chat(rag_messages(query, [passage], cautious=True), temperature=0.0)
        value, _ = parse_committed_value(text)
        if value is not None:
            values.append(value)
    if not values:
        return "VALUE: UNKNOWN\nRATIONALE: No isolated passage produced a committed numeric value."
    counts = Counter(values)
    winner, votes = counts.most_common(1)[0]
    tied = sum(1 for count in counts.values() if count == votes) > 1
    if tied:
        return "VALUE: UNKNOWN\nRATIONALE: Isolated evidence produced a tied conflict."
    return f"VALUE: {winner} {unit}\nRATIONALE: Majority of isolated evidence values."


def validate_against_record(
    item: dict[str, Any],
    answer_text: str,
    covered: bool,
) -> DefenseDecision:
    if not covered:
        return DefenseDecision(answer_text, False, "record_not_covered")
    value, _ = parse_committed_value(answer_text)
    if value is None:
        return DefenseDecision(answer_text, False, "no_numeric_commitment")
    truth = item["value"]
    tol = float(item.get("tolerance", 0.0))
    if not isinstance(truth, (int, float)):
        return DefenseDecision(answer_text, False, "non_numeric_record")
    if abs(value - float(truth)) <= tol:
        return DefenseDecision(answer_text, False, "record_match")
    replacement = (
        "VALUE: UNKNOWN\n"
        f"RATIONALE: The committed value does not match the authoritative system-of-record "
        f"value for {item['item_id']}; verification is required."
    )
    return DefenseDecision(replacement, True, "record_mismatch")
