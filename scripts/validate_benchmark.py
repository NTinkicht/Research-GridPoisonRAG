from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.io import read_jsonl  # noqa: E402


def inside(value: float, lo, hi, tol: float = 0.0) -> bool:
    if lo is not None and value < float(lo) - tol:
        return False
    if hi is not None and value > float(hi) + tol:
        return False
    return True


def main() -> int:
    schema = json.loads((ROOT / "benchmark/schemas/item.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    paths = [
        ROOT / "benchmark/items/tier1_public.jsonl",
        ROOT / "benchmark/items/tier2_assets.jsonl",
        ROOT / "benchmark/items/tier3_conflicts.jsonl",
    ]
    expected = [35, 45, 20]
    all_rows = []
    ids: set[str] = set()
    reviewed = 0

    for path, count in zip(paths, expected):
        rows = read_jsonl(path)
        assert len(rows) == count, f"{path}: expected {count}, got {len(rows)}"
        for row in rows:
            errors = sorted(validator.iter_errors(row), key=lambda e: list(e.path))
            assert not errors, f"{path} {row.get('item_id')}: {errors}"
            assert row["item_id"] not in ids, f"duplicate id {row['item_id']}"
            ids.add(row["item_id"])
            reviewed += int(row["engineer_reviewed"])
            all_rows.append(row)

    assert len(ids) == 100

    t1 = [x for x in all_rows if x["tier"] == 1]
    t2 = [x for x in all_rows if x["tier"] == 2]
    t3 = [x for x in all_rows if x["tier"] == 3]

    for x in t1:
        assert x["source_type"] == "public_authoritative"
        assert x.get("source_url"), f"{x['item_id']}: missing public source URL"
        assert x.get("source_locator"), f"{x['item_id']}: missing source locator"

    for x in t2:
        assert x["source_type"] == "fictional_system_of_record"
        assert x.get("source_url") is None
        assert "fictional" in (x.get("jurisdiction") or "").lower()

    for x in t1 + t2:
        attack = x.get("poison_value_out_of_range")
        assert isinstance(attack, (int, float)), f"{x['item_id']}: missing numeric out-of-range value"
        assert not inside(
            float(attack), x.get("allowable_min"), x.get("allowable_max"), float(x.get("tolerance", 0))
        ), f"{x['item_id']}: attack value is not outside encoded allowable interval"
        wrong = x.get("poison_value_wrong_in_range")
        if wrong is not None:
            assert isinstance(wrong, (int, float))
            assert inside(
                float(wrong), x.get("allowable_min"), x.get("allowable_max"), float(x.get("tolerance", 0))
            ), f"{x['item_id']}: wrong-in-range value is outside interval"
            if isinstance(x["value"], (int, float)):
                assert not math.isclose(
                    float(wrong), float(x["value"]), abs_tol=float(x.get("tolerance", 0)), rel_tol=0
                ), f"{x['item_id']}: wrong-in-range value equals ground truth"

    for x in t3:
        assert x["source_type"] == "legitimate_conflict"
        assert x.get("conflict_alternative_value") is not None
        assert x.get("conflict_alternative_context")
        assert x.get("conflict_alternative_value") != x.get("value")

    clean = read_jsonl(ROOT / "corpus/clean_documents.jsonl")
    poisons = read_jsonl(ROOT / "corpus/poison_variants.jsonl")
    assert len(clean) == 400, f"expected 400 clean docs, got {len(clean)}"
    assert len(poisons) == 400, f"expected 400 poison variants, got {len(poisons)}"
    assert len({x["doc_id"] for x in clean}) == len(clean)
    assert len({x["doc_id"] for x in poisons}) == len(poisons)

    by_item = Counter(x["item_id"] for x in poisons)
    poisonable = {x["item_id"] for x in t1 + t2}
    assert set(by_item) == poisonable
    assert all(by_item[item_id] == 5 for item_id in poisonable)

    allowed_variants = {
        "out_of_range_plain",
        "out_of_range_vendor_bulletin",
        "out_of_range_paraphrase_2",
        "out_of_range_paraphrase_3",
        "wrong_in_range_plain",
    }
    assert {x["variant"] for x in poisons} == allowed_variants

    print(f"PASS: 100 items valid; clean_docs=400; poison_variants=400; engineer-reviewed={reviewed}/100")
    if reviewed < 60:
        print("GATE: fewer than 60 items are engineer-reviewed; do not make engineer-validated claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
