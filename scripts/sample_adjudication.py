from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.io import read_jsonl  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--fraction", type=float, default=0.15)
    p.add_argument("--minimum", type=int, default=300)
    p.add_argument("--seed", type=int, default=20261007)
    p.add_argument("--out", default="results/adjudication_sample.csv")
    args = p.parse_args()

    rows=[]
    for rel in args.files:
        rows.extend(read_jsonl(ROOT / rel))
    if not rows:
        raise SystemExit("No result rows.")

    strata=defaultdict(list)
    for r in rows:
        strata[(r.get("model"),r.get("condition"),r.get("tier"),r.get("label"))].append(r)

    target=min(len(rows), max(args.minimum, round(args.fraction*len(rows))))
    rng=random.Random(args.seed)
    sample=[]
    keys=list(strata)
    # First ensure broad stratum representation where possible.
    rng.shuffle(keys)
    for key in keys:
        if len(sample)>=target:
            break
        sample.append(rng.choice(strata[key]))
    remaining=[r for r in rows if r not in sample]
    rng.shuffle(remaining)
    sample.extend(remaining[:max(0,target-len(sample))])

    out=ROOT/args.out
    out.parent.mkdir(parents=True,exist_ok=True)
    fields=[
        "item_id","tier","model","condition","phrasing","answer","auto_label",
        "reviewer1_label","reviewer2_label","resolution","notes"
    ]
    with out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for r in sample:
            w.writerow({
                "item_id":r.get("item_id"),"tier":r.get("tier"),"model":r.get("model"),
                "condition":r.get("condition"),"phrasing":r.get("phrasing"),
                "answer":r.get("answer"),"auto_label":r.get("label"),
                "reviewer1_label":"","reviewer2_label":"","resolution":"","notes":""
            })
    print(f"Wrote {len(sample)} rows to {out}")


if __name__=="__main__":
    main()
