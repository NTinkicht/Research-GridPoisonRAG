from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gridpoisonrag.grading import grade_answer  # noqa: E402
from gridpoisonrag.io import read_jsonl, write_jsonl  # noqa: E402
from gridpoisonrag.prompts import rag_messages  # noqa: E402
from gridpoisonrag.providers import OpenAICompatClient  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--position", choices=["first", "last"], required=True)
    p.add_argument("--variant", default="out_of_range_plain")
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int)
    args = p.parse_args()

    client = OpenAICompatClient(
        base_url=os.environ["OPENAI_COMPAT_BASE_URL"].rstrip("/"),
        api_key=os.environ["OPENAI_COMPAT_API_KEY"],
        model=args.model,
    )
    items = (
        read_jsonl(ROOT / "benchmark/items/tier1_public.jsonl")
        + read_jsonl(ROOT / "benchmark/items/tier2_assets.jsonl")
    )
    if args.limit:
        items = items[: args.limit]

    clean = read_jsonl(ROOT / "corpus/clean_documents.jsonl")
    poisons = read_jsonl(ROOT / "corpus/poison_variants.jsonl")
    distractors = [d for d in clean if d["kind"] == "distractor"]
    rows = []

    for item in items:
        support = [d for d in clean if d["item_id"] == item["item_id"] and d["kind"] == "support"][:3]
        poison = next(
            d for d in poisons
            if d["item_id"] == item["item_id"] and d["variant"] == args.variant
        )
        # One deterministic on-topic distractor gives a fixed five-passage context.
        candidate = next(
            d for d in distractors
            if item["domain"].lower() in d["text"].lower() and d["item_id"] != item["item_id"]
        )
        clean_context = [d["text"] for d in support] + [candidate["text"]]
        passages = (
            [poison["text"]] + clean_context
            if args.position == "first"
            else clean_context + [poison["text"]]
        )
        assert len(passages) == 5

        # Stage B uses one fixed formal phrasing per item so position, not query wording, is the control.
        query = item["question_formal"]
        answer = client.chat(rag_messages(query, passages, cautious=False), temperature=0.0)
        grade = grade_answer(item, answer)
        rows.append(
            {
                "item_id": item["item_id"],
                "tier": item["tier"],
                "model": args.model,
                "condition": f"STAGE_B_{args.position.upper()}",
                "phrasing": "formal",
                "k": 5,
                "variant": args.variant,
                "poison_count": 1,
                "poison_exposed": True,
                "poison_ranks": [1 if args.position == "first" else 5],
                "answer": answer,
                "label": grade.label,
                "committed_value": grade.committed_value,
                "violation": grade.violation,
            }
        )

    write_jsonl(ROOT / args.out, rows)
    print(f"Wrote {len(rows)} controlled-exposure rows to {args.out}")


if __name__ == "__main__":
    main()
