from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
import sys

from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.io import read_jsonl  # noqa: E402
from gridpoisonrag.metrics import cluster_bootstrap_rate  # noqa: E402
from gridpoisonrag.stats import (  # noqa: E402
    holm_adjust,
    mcnemar_exact,
    paired_cluster_bootstrap_difference,
    paired_items,
)


def rate(rows, fn):
    return sum(bool(fn(r)) for r in rows) / max(len(rows), 1)


def by_item_binary(rows, fn):
    out = defaultdict(list)
    for r in rows:
        out[r["item_id"]].append(int(bool(fn(r))))
    return out


def cluster_bootstrap_trial_rate(rows, fn, resamples=2000, seed=20261007):
    """Cluster bootstrap preserving the trial-level denominator while resampling item IDs."""
    import numpy as np

    grouped = defaultdict(list)
    for r in rows:
        grouped[r["item_id"]].append(int(bool(fn(r))))
    if not grouped:
        return 0.0, 0.0, 0.0
    point = sum(sum(v) for v in grouped.values()) / sum(len(v) for v in grouped.values())
    ids = sorted(grouped)
    rng = np.random.default_rng(seed)
    sims = []
    for _ in range(resamples):
        sampled = rng.choice(ids, size=len(ids), replace=True)
        num = sum(sum(grouped[i]) for i in sampled)
        den = sum(len(grouped[i]) for i in sampled)
        sims.append(num / den if den else 0.0)
    lo, hi = np.quantile(sims, [0.025, 0.975])
    return float(point), float(lo), float(hi)


def clopper_pearson(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    lo = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, n - successes + 1))
    hi = 1.0 if successes == n else float(beta.ppf(1 - alpha / 2, successes + 1, n - successes))
    return lo, hi


def summarize_group(rows):
    exposed = [r for r in rows if r.get("poison_exposed")]
    bvr = rate(rows, lambda r: r.get("violation") is True)
    return {
        "n_trials": len(rows),
        "n_items": len({r["item_id"] for r in rows}),
        "CRR": rate(rows, lambda r: r["label"] == "C"),
        "ASR": rate(rows, lambda r: r["label"] == "A"),
        "CFR": rate(rows, lambda r: r["label"] == "F"),
        "RR": rate(rows, lambda r: r["label"] == "R"),
        "NCR": rate(rows, lambda r: r.get("committed_value") is None),
        "SVR": bvr,
        "BVR": bvr,
        "PoisonAtK": rate(rows, lambda r: r.get("poison_exposed") is True),
        "CAR": rate(exposed, lambda r: r["label"] == "A") if exposed else None,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--out", default="results/analysis_summary.json")
    args = p.parse_args()

    rows = []
    for rel in args.files:
        rows.extend(read_jsonl(ROOT / rel))

    item_map = {}
    for item_file in [
        "benchmark/items/tier1_public.jsonl",
        "benchmark/items/tier2_assets.jsonl",
        "benchmark/items/tier3_conflicts.jsonl",
    ]:
        for item in read_jsonl(ROOT / item_file):
            item_map[item["item_id"]] = item

    groups = defaultdict(list)
    for r in rows:
        groups[(r["condition"], r["model"], r["tier"])].append(r)

    report = {
        "groups": {},
        "intervals": {},
        "natural_exposed": {},
        "wrong_in_range": {},
        "primary_rq2_stage_b": {},
        "primary_rq3_locked": {},
        "secondary_rq3_vs_b2": {},
        "rq3_counts": {},
        "bffr": {},
        "mcnemar_primary": [],
        "mcnemar_any_phrasing": [],
        "d3_coverage": {},
    }

    for (condition, model, tier), group in sorted(groups.items()):
        key = f"{condition}|{model}|T{tier}"
        report["groups"][key] = summarize_group(group)
        for metric, fn in [
            ("ASR", lambda r: r["label"] == "A"),
            ("BVR", lambda r: r.get("violation") is True),
            ("SVR", lambda r: r.get("violation") is True),
            ("CRR", lambda r: r["label"] == "C"),
            ("NCR", lambda r: r.get("committed_value") is None),
        ]:
            vals = by_item_binary(group, fn)
            if vals:
                point, lo, hi = cluster_bootstrap_rate(vals)
                report["intervals"][f"{key}|{metric}"] = {
                    "point": point, "lo95": lo, "hi95": hi
                }

    models = sorted({r["model"] for r in rows})

    # Natural-retrieval exposed-case behavior, reported because suppression of
    # correct answers is more prominent than direct attacker-value adoption.
    natural_conditions = [
        "B2_P1",
        "B2_P3_STRESS",
        "B2_BULLETIN_P1",
        "B2_P1_K2",
    ]
    for model in models:
        for condition in natural_conditions:
            for tier in [1, 2]:
                subset = [
                    r for r in rows
                    if r["model"] == model and r["tier"] == tier and r["condition"] == condition
                ]
                if not subset:
                    continue
                exposed = [r for r in subset if r.get("poison_exposed")]
                key = f"{model}|{condition}|T{tier}"
                _, car_lo, car_hi = cluster_bootstrap_trial_rate(
                    exposed, lambda r: r["label"] == "A"
                ) if exposed else (None, None, None)
                report["natural_exposed"][key] = {
                    "n_trials": len(subset),
                    "n_exposed": len(exposed),
                    "n_correct_exposed": sum(r["label"] == "C" for r in exposed),
                    "n_attacker_exposed": sum(r["label"] == "A" for r in exposed),
                    "n_noncommit_exposed": sum(r.get("committed_value") is None for r in exposed),
                    "correct_given_exposure": rate(exposed, lambda r: r["label"] == "C") if exposed else None,
                    "CAR": rate(exposed, lambda r: r["label"] == "A") if exposed else None,
                    "car_cluster_lo95": car_lo,
                    "car_cluster_hi95": car_hi,
                    "attacker_trial_keys": sorted(
                        f'{r["item_id"]}|{r.get("phrasing")}'
                        for r in exposed if r["label"] == "A"
                    ),
                }

    # Secondary wrong-but-in-range condition: raw A labels intentionally refer
    # to the primary out-of-range poison, so compute direct adoption separately.
    for model in models:
        subset = [
            r for r in rows
            if r["model"] == model and r["condition"] == "B2_WRONG_IN_RANGE_P1"
        ]
        if not subset:
            continue
        eligible = []
        adopted = []
        for r in subset:
            item = item_map[r["item_id"]]
            target = item.get("poison_value_wrong_in_range")
            if not isinstance(target, (int, float)):
                continue
            eligible.append(r)
            value = r.get("committed_value")
            tol = float(item.get("tolerance", 0.0))
            if isinstance(value, (int, float)) and math.isclose(
                float(value), float(target), abs_tol=tol, rel_tol=0.0
            ):
                adopted.append(r)
        exposed = [r for r in eligible if r.get("poison_exposed")]
        adopted_exposed = [r for r in adopted if r.get("poison_exposed")]
        by_tier = {}
        for tier in [1, 2]:
            eligible_t = [r for r in eligible if r["tier"] == tier]
            exposed_t = [r for r in eligible_t if r.get("poison_exposed")]
            adopted_t = [r for r in adopted_exposed if r["tier"] == tier]
            by_tier[f"T{tier}"] = {
                "n_trials": len(eligible_t),
                "n_exposed": len(exposed_t),
                "n_adopted_exposed": len(adopted_t),
            }
        report["wrong_in_range"][model] = {
            "n_trials": len(eligible),
            "n_exposed": len(exposed),
            "n_adopted": len(adopted),
            "n_adopted_exposed": len(adopted_exposed),
            "adoption_rate": len(adopted) / max(len(eligible), 1),
            "CAR": len(adopted_exposed) / max(len(exposed), 1),
            "by_tier": by_tier,
        }

    # Primary RQ2: attacker-value adoption under forced exposure, stratified by
    # position and tier. Stage B has one formal query per item, so exact
    # binomial intervals are also meaningful and avoid degenerate [0,0] bounds.
    for model in models:
        for condition in ["STAGE_B_FIRST", "STAGE_B_LAST"]:
            for tier in [1, 2]:
                subset = [
                    r for r in rows
                    if r["model"] == model and r["tier"] == tier and r["condition"] == condition
                ]
                if not subset:
                    continue
                vals = by_item_binary(subset, lambda r: r["label"] == "A")
                point, lo, hi = cluster_bootstrap_rate(vals)
                successes = sum(r["label"] == "A" for r in subset)
                cp_lo, cp_hi = clopper_pearson(successes, len(subset))
                report["primary_rq2_stage_b"][f"{model}|{condition}|T{tier}"] = {
                    "adoption": point,
                    "lo95": lo,
                    "hi95": hi,
                    "exact_lo95": cp_lo,
                    "exact_hi95": cp_hi,
                    "n_success": successes,
                    "n_items": len(vals),
                }

    # Primary RQ3 exactly follows the methods lock: D3@70 versus D1 and D2.
    primary_tests = []
    for model in models:
        d3 = [
            r for r in rows
            if r["model"] == model and r["tier"] in {1, 2}
            and r["condition"] == "D3_P3_70"
        ]
        if not d3:
            continue
        for comparator in ["D1_P3", "D2_P3"]:
            base = [
                r for r in rows
                if r["model"] == model and r["tier"] in {1, 2}
                and r["condition"] == comparator
            ]
            if not base:
                continue
            point, lo, hi = paired_cluster_bootstrap_difference(
                base, d3, lambda r: r.get("violation") is True
            )
            report["primary_rq3_locked"][f"{model}|{comparator}"] = {
                "delta_bvr": point,
                "lo95": lo,
                "hi95": hi,
                "interpretation": f"{comparator} BVR minus D3_P3_70 BVR",
            }
            pairs = paired_items(base, d3, lambda r: r.get("violation") is True)
            result = mcnemar_exact(pairs)
            primary_tests.append({
                "model": model,
                "comparator": comparator,
                "b": result.b,
                "c": result.c,
                "p": result.p_value,
            })

    if primary_tests:
        adjusted = holm_adjust([x["p"] for x in primary_tests])
        for x, adj in zip(primary_tests, adjusted):
            x["p_holm"] = adj
        report["mcnemar_primary"] = primary_tests

    # Sensitivity: an item violates if either phrasing violates.
    def any_items(rs):
        grouped = defaultdict(list)
        for r in rs:
            grouped[r["item_id"]].append(r.get("violation") is True)
        return {item: any(vals) for item, vals in grouped.items()}

    sensitivity = []
    for model in models:
        d3_rows = [
            r for r in rows
            if r["model"] == model and r["tier"] in {1, 2}
            and r["condition"] == "D3_P3_70"
        ]
        if not d3_rows:
            continue
        d3_any = any_items(d3_rows)
        for comparator in ["D1_P3", "D2_P3"]:
            base_rows = [
                r for r in rows
                if r["model"] == model and r["tier"] in {1, 2}
                and r["condition"] == comparator
            ]
            if not base_rows:
                continue
            base_any = any_items(base_rows)
            common = sorted(set(base_any) & set(d3_any))
            result = mcnemar_exact((base_any[i], d3_any[i]) for i in common)
            sensitivity.append({
                "model": model,
                "comparator": comparator,
                "b": result.b,
                "c": result.c,
                "p": result.p_value,
            })
    if sensitivity:
        adjusted = holm_adjust([x["p"] for x in sensitivity])
        for x, adj in zip(sensitivity, adjusted):
            x["p_holm"] = adj
        report["mcnemar_any_phrasing"] = sensitivity

    # Secondary descriptive comparisons against the poisoned conflict-aware B2 stress baseline.
    secondary_defenses = ["D1_P3", "D2_P3", "D3_P3_40", "D3_P3_70", "D3_P3_100"]
    for model in models:
        base = [
            r for r in rows
            if r["model"] == model and r["tier"] in {1, 2}
            and r["condition"] == "B2_P3_STRESS"
        ]
        if not base:
            continue
        report["rq3_counts"][model] = {}
        for condition in ["B2_P3_STRESS"] + secondary_defenses:
            subset = [
                r for r in rows
                if r["model"] == model and r["tier"] in {1, 2}
                and r["condition"] == condition
            ]
            if subset:
                report["rq3_counts"][model][condition] = {
                    "n_trials": len(subset),
                    "n_violations": sum(r.get("violation") is True for r in subset),
                }
        for defense in secondary_defenses:
            dr = [
                r for r in rows
                if r["model"] == model and r["tier"] in {1, 2}
                and r["condition"] == defense
            ]
            if not dr:
                continue
            point, lo, hi = paired_cluster_bootstrap_difference(
                base, dr, lambda r: r.get("violation") is True
            )
            report["secondary_rq3_vs_b2"][f"{model}|{defense}"] = {
                "delta_bvr": point, "lo95": lo, "hi95": hi
            }

    # Realized deterministic hash coverage (identical across model families).
    if models:
        first_model = models[0]
        for cov in [40, 70, 100]:
            poison_rows = [
                r for r in rows
                if r["model"] == first_model and r["tier"] in {1, 2}
                and r["condition"] == f"D3_P3_{cov}"
            ]
            conflict_rows = [
                r for r in rows
                if r["model"] == first_model and r["tier"] == 3
                and r["condition"] == f"D3_CONFLICT_{cov}"
            ]
            if poison_rows or conflict_rows:
                report["d3_coverage"][str(cov)] = {
                    "poisonable_covered_items": len({
                        r["item_id"] for r in poison_rows if r.get("d3_covered")
                    }),
                    "conflict_covered_items": len({
                        r["item_id"] for r in conflict_rows if r.get("d3_covered")
                    }),
                }

    # D3 benign-conflict false-flag rate. Condition on clean-RAG correctness so
    # a false flag is charged only when D3 changes an otherwise-correct answer.
    for model in models:
        baseline = [
            r for r in rows
            if r["model"] == model and r["tier"] == 3 and r["condition"] == "B1_CONFLICT"
        ]
        baseline_by_trial = {
            (r["item_id"], r.get("phrasing")): r for r in baseline
        }
        for condition in ["D3_CONFLICT_40", "D3_CONFLICT_70", "D3_CONFLICT_100"]:
            subset = [
                r for r in rows
                if r["model"] == model and r["tier"] == 3 and r["condition"] == condition
            ]
            eligible = [
                r for r in subset
                if baseline_by_trial.get((r["item_id"], r.get("phrasing")), {}).get("label") == "C"
            ]
            if eligible:
                flagged = [bool(r.get("d3_flagged")) for r in eligible]
                report["bffr"][f"{model}|{condition}"] = {
                    "rate": sum(flagged) / len(flagged),
                    "n_trials": len(flagged),
                    "n_items": len({r["item_id"] for r in eligible}),
                    "definition": "D3 flag conditional on clean-RAG correct benign-conflict answer",
                }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
