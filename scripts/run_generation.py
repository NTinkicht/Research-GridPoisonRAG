from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.defenses import isolate_then_aggregate, validate_against_record  # noqa: E402
from gridpoisonrag.grading import grade_answer  # noqa: E402
from gridpoisonrag.io import read_jsonl, write_jsonl  # noqa: E402
from gridpoisonrag.prompts import closed_book_messages, rag_messages  # noqa: E402
from gridpoisonrag.providers import OpenAICompatClient  # noqa: E402
from gridpoisonrag.retrieval import DenseRetriever  # noqa: E402


def select_poison(poison_docs, item_id, variant, count):
    docs = [d for d in poison_docs if d["item_id"] == item_id]
    if count == 3 and variant == "unsafe_plain":
        wanted = {"unsafe_plain", "unsafe_paraphrase_2", "unsafe_paraphrase_3"}
        return [d for d in docs if d["variant"] in wanted][:3]
    return [d for d in docs if d["variant"] == variant][:count]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--condition", choices=["B0", "B1", "B2", "D1", "D2"], required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--variant", default="unsafe_plain")
    p.add_argument("--poison-count", type=int, default=1)
    p.add_argument("--tier", choices=["1", "2", "both"], default="both")
    p.add_argument("--limit", type=int)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    client = OpenAICompatClient(
        base_url=os.environ["OPENAI_COMPAT_BASE_URL"].rstrip("/"),
        api_key=os.environ["OPENAI_COMPAT_API_KEY"],
        model=args.model,
    )
    items = read_jsonl(ROOT / "benchmark/items/tier1_public.jsonl") + read_jsonl(
        ROOT / "benchmark/items/tier2_assets.jsonl"
    )
    if args.tier != "both":
        items = [x for x in items if x["tier"] == int(args.tier)]
    if args.limit:
        items = items[: args.limit]

    clean = read_jsonl(ROOT / "corpus/clean_documents.jsonl")
    poisons = read_jsonl(ROOT / "corpus/poison_variants.jsonl")
    rows = []
    for item in items:
        extra = [] if args.condition in {"B0", "B1"} else select_poison(
            poisons, item["item_id"], args.variant, args.poison_count
        )
        corpus = clean + extra
        retriever = None if args.condition == "B0" else DenseRetriever(
            corpus, "sentence-transformers/all-MiniLM-L6-v2"
        )
        for phrasing, query in [("formal", item["question_formal"]), ("field", item["question_field"])]:
            if args.condition == "B0":
                hits = []
                answer = client.chat(closed_book_messages(query), temperature=0.0)
            else:
                hits = retriever.search(query, args.k)
                passages = [h.document["text"] for h in hits]
                if args.condition == "D2":
                    answer = isolate_then_aggregate(client, query, passages, item["unit"])
                else:
                    answer = client.chat(
                        rag_messages(query, passages, cautious=args.condition == "D1"),
                        temperature=0.0,
                    )
            grade = grade_answer(item, answer)
            poison_ranks = [h.rank for h in hits if h.document.get("kind") == "poison"]
            rows.append(
                {
                    "item_id": item["item_id"],
                    "tier": item["tier"],
                    "model": args.model,
                    "condition": args.condition,
                    "phrasing": phrasing,
                    "k": args.k,
                    "variant": args.variant if extra else None,
                    "poison_count": len(extra),
                    "poison_exposed": bool(poison_ranks),
                    "poison_ranks": poison_ranks,
                    "answer": answer,
                    "label": grade.label,
                    "committed_value": grade.committed_value,
                    "violation": grade.violation,
                }
            )
    write_jsonl(ROOT / args.out, rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
