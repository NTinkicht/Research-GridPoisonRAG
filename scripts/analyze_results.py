from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.io import read_jsonl  # noqa: E402
from gridpoisonrag.metrics import cluster_bootstrap_rate, summarize  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    args = p.parse_args()
    rows = []
    for file in args.files:
        rows.extend(read_jsonl(ROOT / file))

    groups = defaultdict(list)
    for row in rows:
        groups[(row["condition"], row["model"], row["tier"])].append(row)

    for key, group in sorted(groups.items()):
        summary = summarize([r["label"] for r in group], [r["violation"] for r in group])
        print(key, summary)
        by_item = defaultdict(list)
        for r in group:
            by_item[r["item_id"]].append(int(r["label"] == "A"))
        if by_item:
            print("  ASR bootstrap:", cluster_bootstrap_rate(by_item))


if __name__ == "__main__":
    main()
