from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.io import read_jsonl, write_jsonl  # noqa: E402
from gridpoisonrag.retrieval import DenseRetriever  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    p.add_argument("--variant", default="unsafe_plain")
    p.add_argument("--poison-count", type=int, choices=[1, 3], default=1)
    p.add_argument("--out", default="results/stage_a.jsonl")
    args = p.parse_args()

    items = read_jsonl(ROOT / "benchmark/items/tier1_public.jsonl") + read_jsonl(
        ROOT / "benchmark/items/tier2_assets.jsonl"
    )
    clean = read_jsonl(ROOT / "corpus/clean_documents.jsonl")
    poisons = read_jsonl(ROOT / "corpus/poison_variants.jsonl")
    by_item = {}
    for d in poisons:
        by_item.setdefault(d["item_id"], []).append(d)

    rows = []
    for item in items:
        candidates = [d for d in by_item[item["item_id"]] if d["variant"] == args.variant]
        if args.poison_count == 3 and args.variant == "unsafe_plain":
            candidates = [
                d for d in by_item[item["item_id"]]
                if d["variant"] in {"unsafe_plain", "unsafe_paraphrase_2", "unsafe_paraphrase_3"}
            ][:3]
        else:
            candidates = candidates[:1]
        corpus = clean + candidates
        retriever = DenseRetriever(corpus, args.model)
        for phrasing_name, query in [
            ("formal", item["question_formal"]),
            ("field", item["question_field"]),
        ]:
            hits = retriever.search(query, 10)
            poison_ranks = [h.rank for h in hits if h.document.get("kind") == "poison"]
            rows.append(
                {
                    "item_id": item["item_id"],
                    "tier": item["tier"],
                    "phrasing": phrasing_name,
                    "query": query,
                    "poison_count": args.poison_count,
                    "variant": args.variant,
                    "poison_ranks_top10": poison_ranks,
                    "poison_at_1": int(any(r <= 1 for r in poison_ranks)),
                    "poison_at_2": int(any(r <= 2 for r in poison_ranks)),
                    "poison_at_5": int(any(r <= 5 for r in poison_ranks)),
                    "poison_at_10": int(any(r <= 10 for r in poison_ranks)),
                }
            )
    out = ROOT / args.out
    write_jsonl(out, rows)
    print(json.dumps({"rows": len(rows), "out": str(out)}))


if __name__ == "__main__":
    main()
