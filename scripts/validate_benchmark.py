from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.io import read_jsonl  # noqa: E402


def main() -> int:
    schema = json.loads((ROOT / "benchmark/schemas/item.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    paths = [
        ROOT / "benchmark/items/tier1_public.jsonl",
        ROOT / "benchmark/items/tier2_assets.jsonl",
        ROOT / "benchmark/items/tier3_conflicts.jsonl",
    ]
    expected = [35, 45, 20]
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
    assert len(ids) == 100
    print(f"PASS: 100 items valid; engineer-reviewed={reviewed}/100")
    if reviewed < 60:
        print("GATE: fewer than 60 items are engineer-reviewed; do not make engineer-validated claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
