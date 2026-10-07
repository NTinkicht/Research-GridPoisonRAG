from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "benchmark/items/tier1_public.jsonl",
    "benchmark/items/tier2_assets.jsonl",
    "benchmark/items/tier3_conflicts.jsonl",
    "benchmark/asset_register/fictional_asset_register.json",
    "benchmark/system_of_record/validation_table.json",
    "benchmark/schemas/item.schema.json",
    "benchmark/sources/public_sources.yaml",
    "corpus/clean_documents.jsonl",
    "corpus/poison_variants.jsonl",
    "configs/experiments.yaml",
    "configs/models.yaml",
]


def main() -> None:
    manifest = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Creating this file does not imply human engineer approval; validate review status first.",
        "sha256": {},
    }
    for rel in FILES:
        data = (ROOT / rel).read_bytes()
        manifest["sha256"][rel] = hashlib.sha256(data).hexdigest()
    out = ROOT / "benchmark/FROZEN_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
