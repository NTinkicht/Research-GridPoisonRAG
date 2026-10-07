from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gridpoisonrag.io import read_jsonl  # noqa: E402


def summarize(path: Path) -> dict:
    rows = read_jsonl(path)
    out = {"file": str(path.relative_to(ROOT)), "n": len(rows)}
    for tier in [1, 2, "all"]:
        subset = rows if tier == "all" else [r for r in rows if r["tier"] == tier]
        label = f"tier_{tier}"
        out[label] = {
            f"poison_at_{k}": sum(r[f"poison_at_{k}"] for r in subset) / max(len(subset), 1)
            for k in [1, 2, 5, 10]
        }
        out[label]["n"] = len(subset)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--out", default="results/stage_a_summary.json")
    args = p.parse_args()
    report = {"runs": [summarize(ROOT / f) for f in args.files]}
    path = ROOT / args.out
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
