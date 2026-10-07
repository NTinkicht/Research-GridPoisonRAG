from __future__ import annotations

import argparse
import hashlib
import json
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
    p.add_argument("--run-label", help="Condition label; defaults to D3_<coverage percent>")
    args = p.parse_args()

    items = {
        x["item_id"]: x
        for x in (
            read_jsonl(ROOT / "benchmark/items/tier1_public.jsonl")
            + read_jsonl(ROOT / "benchmark/items/tier2_assets.jsonl")
            + read_jsonl(ROOT / "benchmark/items/tier3_conflicts.jsonl")
        )
    }
    record_obj = json.loads(
        (ROOT / "benchmark/system_of_record/validation_table.json").read_text(encoding="utf-8")
    )
    record = {x["item_id"]: x for x in record_obj["entries"]}

    rows = []
    for row in read_jsonl(ROOT / args.input):
        item = items[row["item_id"]]
        is_covered = covered(item["item_id"], args.coverage)
        record_value = record.get(item["item_id"], {}).get("record_value")
        decision = validate_against_record(item, row["answer"], is_covered, record_value)
        grade = grade_answer(item, decision.answer)
        rows.append(
            {
                **row,
                "condition": args.run_label or f"D3_{int(args.coverage*100)}",
                "d3_covered": is_covered,
                "d3_record_value": record_value,
                "d3_record_scope": record.get(item["item_id"], {}).get("scope"),
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
