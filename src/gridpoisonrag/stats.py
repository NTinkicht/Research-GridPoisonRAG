from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.stats import binomtest


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm family-wise-error adjustment preserving input order."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [1.0] * m
    running = 0.0
    for rank, (idx, p) in enumerate(indexed):
        val = min(1.0, (m - rank) * p)
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


@dataclass(frozen=True)
class McNemarResult:
    b: int
    c: int
    p_value: float


def mcnemar_exact(pairs: Iterable[tuple[bool, bool]]) -> McNemarResult:
    """Exact paired McNemar test.

    Each pair is (baseline_failure, defense_failure). b counts baseline-only failures and
    c counts defense-only failures.
    """
    b = c = 0
    for baseline_failure, defense_failure in pairs:
        if baseline_failure and not defense_failure:
            b += 1
        elif defense_failure and not baseline_failure:
            c += 1
    discordant = b + c
    if discordant == 0:
        return McNemarResult(b, c, 1.0)
    p = binomtest(min(b, c), discordant, 0.5, alternative="two-sided").pvalue
    return McNemarResult(b, c, float(p))


def item_majority(rows: list[dict], predicate) -> dict[str, bool]:
    grouped: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        grouped[row["item_id"]].append(bool(predicate(row)))
    return {item: sum(vals) > len(vals) / 2 for item, vals in grouped.items()}


def paired_items(base_rows: list[dict], defense_rows: list[dict], predicate):
    base = item_majority(base_rows, predicate)
    defense = item_majority(defense_rows, predicate)
    common = sorted(set(base) & set(defense))
    return [(base[i], defense[i]) for i in common]
