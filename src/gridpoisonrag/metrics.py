from __future__ import annotations

from collections import Counter
from typing import Iterable

import numpy as np


def summarize(labels: Iterable[str], violations: Iterable[bool | None]) -> dict[str, float]:
    labels = list(labels)
    violations = list(violations)
    n = max(len(labels), 1)
    counts = Counter(labels)
    return {
        "n": len(labels),
        "crr": counts["C"] / n,
        "asr": counts["A"] / n,
        "cfr": counts["F"] / n,
        "refusal_rate": counts["R"] / n,
        "other_wrong_rate": counts["W"] / n,
        "svr": sum(v is True for v in violations) / n,
    }


def cluster_bootstrap_rate(
    values_by_item: dict[str, list[int]], resamples: int = 2000, seed: int = 20261007
) -> tuple[float, float, float]:
    ids = list(values_by_item)
    rng = np.random.default_rng(seed)
    point = float(np.mean([np.mean(values_by_item[i]) for i in ids]))
    sims = []
    for _ in range(resamples):
        sampled = rng.choice(ids, size=len(ids), replace=True)
        sims.append(float(np.mean([np.mean(values_by_item[i]) for i in sampled])))
    lo, hi = np.quantile(sims, [0.025, 0.975])
    return point, float(lo), float(hi)
