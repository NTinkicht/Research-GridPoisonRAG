from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.defenses import validate_against_record  # noqa: E402
from gridpoisonrag.grading import grade_answer  # noqa: E402
from gridpoisonrag.io import read_jsonl, write_jsonl  # noqa: E402


def covered(item_id: str, coverage: float) -> bool:
    bucket = int(hashlib.sha256(item_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return bucket < coverage


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--coverage", type=float, choices=[0.4, 0.7, 1.0], required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    items = {
        x["item_id"]: x
        for x in (
            read_jsonl(ROOT / "benchmark/items/tier1_public.jsonl")
            + read_jsonl(ROOT / "benchmark/items/tier2_assets.jsonl")
        )
    }
    rows = []
    for row in read_jsonl(ROOT / args.input):
        item = items[row["item_id"]]
        decision = validate_against_record(item, row["answer"], covered(item["item_id"], args.coverage))
        grade = grade_answer(item, decision.answer)
        rows.append(
            {
                **row,
                "condition": f"D3_{int(args.coverage*100)}",
                "d3_flagged": decision.flagged,
                "d3_reason": decision.reason,
                "answer": decision.answer,
                "label": grade.label,
                "committed_value": grade.committed_value,
                "violation": grade.violation,
            }
        )
    write_jsonl(ROOT / args.out, rows)


if __name__ == "__main__":
    main()
