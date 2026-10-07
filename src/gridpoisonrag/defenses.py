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
        return "VALUE: UNKNOWN\nRATIONALE: Sources conflict; isolated evidence produced a tied value."
    return f"VALUE: {winner} {unit}\nRATIONALE: Majority of isolated evidence values."


def validate_against_record(
    item: dict[str, Any],
    answer_text: str,
    covered: bool,
    record_value: float | None = None,
) -> DefenseDecision:
    """D3 validation against an independent structured record.

    record_value deliberately need not equal the benchmark label. This lets the study measure
    false flags when a simplified system of record omits legitimate jurisdictional variants.
    """
    if not covered:
        return DefenseDecision(answer_text, False, "record_not_covered")
    value, _ = parse_committed_value(answer_text)
    if value is None:
        return DefenseDecision(answer_text, False, "no_numeric_commitment")
    if record_value is None:
        record_value = item["value"]
    tol = float(item.get("tolerance", 0.0))
    if not isinstance(record_value, (int, float)):
        return DefenseDecision(answer_text, False, "non_numeric_record")
    if abs(value - float(record_value)) <= tol:
        return DefenseDecision(answer_text, False, "record_match")
    replacement = (
        "VALUE: UNKNOWN\n"
        f"RATIONALE: Conflict with the covered system-of-record entry for {item['item_id']}; "
        "verify the applicable record before use."
    )
    return DefenseDecision(replacement, True, "record_mismatch")
