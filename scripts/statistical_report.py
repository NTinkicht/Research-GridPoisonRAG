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
from gridpoisonrag.stats import holm_adjust, mcnemar_exact, paired_items  # noqa: E402


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
        "CAR": (
            rate(exposed, lambda r: r["label"] == "A") if exposed else None
        ),
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

    report = {"groups": {}, "intervals": {}, "mcnemar": []}
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

    # Defense-vs-B2 paired McNemar tests by model and tier on violation outcome.
    tests = []
    for model in sorted({r["model"] for r in rows}):
        for tier in [1, 2]:
            base = [r for r in rows if r["model"] == model and r["tier"] == tier and r["condition"] == "B2"]
            if not base:
                continue
            for defense in ["D1", "D2", "D3_40", "D3_70", "D3_100"]:
                dr = [r for r in rows if r["model"] == model and r["tier"] == tier and r["condition"] == defense]
                if not dr:
                    continue
                pairs = paired_items(base, dr, lambda r: r.get("violation") is True)
                result = mcnemar_exact(pairs)
                tests.append({
                    "model": model, "tier": tier, "defense": defense,
                    "b": result.b, "c": result.c, "p": result.p_value
                })
    if tests:
        adjusted = holm_adjust([x["p"] for x in tests])
        for x, adj in zip(tests, adjusted):
            x["p_holm"] = adj
        report["mcnemar"] = tests

    # Primary RQ2 descriptive endpoint: CAR Tier 1 vs Tier 2 under B2.
    primary = {}
    for model in sorted({r["model"] for r in rows}):
        for tier in [1, 2]:
            subset = [
                r for r in rows
                if r["model"] == model and r["tier"] == tier
                and r["condition"] == "B2" and r.get("poison_exposed")
            ]
            primary[f"{model}|T{tier}|CAR"] = (
                rate(subset, lambda r: r["label"] == "A") if subset else None
            )
    report["primary_car"] = primary

    # Tier-3 benign-conflict false-flag rate for D3 conditions.
    bffr = {}
    for model in sorted({r["model"] for r in rows}):
        for condition in ["D3_40", "D3_70", "D3_100"]:
            subset = [
                r for r in rows
                if r["model"] == model and r["tier"] == 3 and r["condition"] == condition
            ]
            if subset:
                flagged = [
                    bool(r.get("d3_flagged")) or r.get("label") in {"F", "R"}
                    for r in subset
                ]
                bffr[f"{model}|{condition}"] = sum(flagged) / len(flagged)
    report["bffr"] = bffr

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
