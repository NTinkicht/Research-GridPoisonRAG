from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

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


def summarize_group(rows):
    exposed = [r for r in rows if r.get("poison_exposed")]
    return {
        "n_trials": len(rows),
        "n_items": len({r["item_id"] for r in rows}),
        "CRR": rate(rows, lambda r: r["label"] == "C"),
        "ASR": rate(rows, lambda r: r["label"] == "A"),
        "CFR": rate(rows, lambda r: r["label"] == "F"),
        "RR": rate(rows, lambda r: r["label"] == "R"),
        "SVR": rate(rows, lambda r: r.get("violation") is True),
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

    groups = defaultdict(list)
    for r in rows:
        groups[(r["condition"], r["model"], r["tier"])].append(r)

    report = {
        "groups": {},
        "intervals": {},
        "primary_rq2_stage_b": {},
        "primary_rq3_delta_svr": {},
        "bffr": {},
        "mcnemar": [],
    }

    for (condition, model, tier), group in sorted(groups.items()):
        key = f"{condition}|{model}|T{tier}"
        report["groups"][key] = summarize_group(group)
        for metric, fn in [
            ("ASR", lambda r: r["label"] == "A"),
            ("SVR", lambda r: r.get("violation") is True),
            ("CRR", lambda r: r["label"] == "C"),
        ]:
            vals = by_item_binary(group, fn)
            if vals:
                point, lo, hi = cluster_bootstrap_rate(vals)
                report["intervals"][f"{key}|{metric}"] = {
                    "point": point, "lo95": lo, "hi95": hi
                }

    models = sorted({r["model"] for r in rows})

    # Primary RQ2: adoption under forced exposure, stratified by position and tier.
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
                report["primary_rq2_stage_b"][f"{model}|{condition}|T{tier}"] = {
                    "adoption": point, "lo95": lo, "hi95": hi, "n_items": len(vals)
                }

    # Primary RQ3: paired violation-rate reduction under the P3 stress condition.
    defense_names = ["D1_P3", "D2_P3", "D3_P3_40", "D3_P3_70", "D3_P3_100"]
    tests = []
    for model in models:
        base = [
            r for r in rows
            if r["model"] == model and r["tier"] in {1, 2}
            and r["condition"] == "B2_P3_STRESS"
        ]
        if not base:
            continue
        for defense in defense_names:
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
            report["primary_rq3_delta_svr"][f"{model}|{defense}"] = {
                "delta_svr": point, "lo95": lo, "hi95": hi
            }
            pairs = paired_items(base, dr, lambda r: r.get("violation") is True)
            result = mcnemar_exact(pairs)
            tests.append({
                "model": model, "defense": defense,
                "b": result.b, "c": result.c, "p": result.p_value
            })

    if tests:
        adjusted = holm_adjust([x["p"] for x in tests])
        for x, adj in zip(tests, adjusted):
            x["p_holm"] = adj
        report["mcnemar"] = tests

    # D3 benign-conflict false-flag rate.
    # A false flag is only meaningful when clean RAG first produced the correct
    # context-specific answer. Condition on those B1_CONFLICT trials, then ask
    # whether D3 flags them because the simplified record lacks the applicable variant.
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
