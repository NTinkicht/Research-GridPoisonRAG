from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rank_bm25 import BM25Okapi

from gridpoisonrag.io import read_jsonl
from gridpoisonrag.retrieval import DenseRetriever


MODEL_KEYS = [
    "qwen_qwen3-8b",
    "mistralai_mistral-small-3.2-24b-instruct",
    "openai_gpt-5.6-luna",
]


def select_poisons(all_poisons: list[dict], item_id: str, variant: str, count: int) -> list[dict]:
    docs = [d for d in all_poisons if d["item_id"] == item_id]
    if count == 3 and variant == "out_of_range_plain":
        wanted = {"out_of_range_plain", "out_of_range_paraphrase_2", "out_of_range_paraphrase_3"}
        return [d for d in docs if d["variant"] in wanted][:3]
    return [d for d in docs if d["variant"] == variant][:count]


def query_for(item: dict, phrasing: str) -> str:
    return item["question_formal"] if phrasing == "formal" else item["question_field"]


def dense_audit(items_by_id: dict[str, dict], clean: list[dict], poisons: list[dict]) -> dict:
    retriever = DenseRetriever(clean, "sentence-transformers/all-MiniLM-L6-v2")
    specs = [
        ("main_b2_p1.jsonl", "out_of_range_plain", 1),
        ("main_b2_p3.jsonl", "out_of_range_plain", 3),
        ("dev_bulletin.jsonl", "out_of_range_vendor_bulletin", 1),
        ("dev_k2.jsonl", "out_of_range_plain", 1),
    ]
    checked = 0
    mismatches: list[dict] = []
    rows: list[dict] = []
    seen: set[tuple] = set()

    for model_key in MODEL_KEYS:
        for filename, variant, count in specs:
            path = ROOT / "results" / model_key / filename
            if not path.exists():
                continue
            for old in read_jsonl(path):
                item = items_by_id[old["item_id"]]
                query = query_for(item, old["phrasing"])
                extra = select_poisons(poisons, item["item_id"], variant, count)
                hits = retriever.search(query, 10, extra_documents=extra)
                reproduced = [h.rank for h in hits if h.document.get("kind") == "poison" and h.rank <= old["k"]]
                expected = list(old.get("poison_ranks") or [])
                checked += 1
                if reproduced != expected:
                    mismatches.append(
                        {
                            "model_key": model_key,
                            "file": filename,
                            "item_id": item["item_id"],
                            "phrasing": old["phrasing"],
                            "k": old["k"],
                            "expected": expected,
                            "reproduced": reproduced,
                        }
                    )

                key = (filename, item["item_id"], old["phrasing"])
                if key not in seen:
                    seen.add(key)
                    rows.append(
                        {
                            "condition_file": filename,
                            "variant": variant,
                            "poison_count": count,
                            "item_id": item["item_id"],
                            "tier": item["tier"],
                            "phrasing": old["phrasing"],
                            "top10": [
                                {
                                    "rank": h.rank,
                                    "doc_id": h.document.get("doc_id"),
                                    "item_id": h.document.get("item_id"),
                                    "kind": h.document.get("kind"),
                                    "score": h.score,
                                }
                                for h in hits
                            ],
                        }
                    )

    return {
        "checked_generation_rows": checked,
        "rank_drift_count": len(mismatches),
        "rank_drift": mismatches,
        "unique_retrieval_rows": rows,
    }


def bm25_audit(items: list[dict], clean: list[dict], poisons: list[dict]) -> tuple[list[dict], dict]:
    rows = []
    clean_index = {d["doc_id"]: i for i, d in enumerate(clean)}
    tie_queries = 0
    clean_first_exposure = {2: 0, 5: 0}
    poison_first_exposure = {2: 0, 5: 0}

    for item in items:
        poison = select_poisons(poisons, item["item_id"], "out_of_range_plain", 1)[0]
        docs = clean + [poison]
        poison_idx = len(docs) - 1
        twin_idx = clean_index[poison["paired_clean_doc_id"]]
        tokens = [d["text"].lower().split() for d in docs]
        index = BM25Okapi(tokens)
        for phrasing in ("formal", "field"):
            query = query_for(item, phrasing)
            scores = index.get_scores(query.lower().split())
            exact_twin_tie = abs(float(scores[poison_idx]) - float(scores[twin_idx])) <= 1e-12
            tie_queries += int(exact_twin_tie)

            clean_first_order = sorted(
                range(len(docs)), key=lambda i: (-float(scores[i]), i)
            )[:10]
            poison_first_order = sorted(
                range(len(docs)),
                key=lambda i: (-float(scores[i]), 0 if i == poison_idx else 1, i),
            )[:10]

            for k in (2, 5):
                clean_first_exposure[k] += int(poison_idx in clean_first_order[:k])
                poison_first_exposure[k] += int(poison_idx in poison_first_order[:k])

            top = [
                (rank + 1, float(scores[i]), docs[i])
                for rank, i in enumerate(clean_first_order)
            ]
            row = {
                "item_id": item["item_id"],
                "tier": item["tier"],
                "phrasing": phrasing,
                "poison_clean_twin_exact_score_tie": exact_twin_tie,
                "top10": [
                    {
                        "rank": rank,
                        "doc_id": doc.get("doc_id"),
                        "item_id": doc.get("item_id"),
                        "kind": doc.get("kind"),
                        "score": score,
                    }
                    for rank, score, doc in top
                ],
            }
            for k in (2, 5):
                ctx = [doc for rank, _score, doc in top if rank <= k]
                row[f"poison_exposed_k{k}"] = any(d.get("kind") == "poison" for d in ctx)
                row[f"clean_same_item_k{k}"] = sum(
                    1
                    for d in ctx
                    if d.get("kind") != "poison" and d.get("item_id") == item["item_id"]
                )
            rows.append(row)

    sensitivity = {
        "total_queries": len(rows),
        "exact_poison_clean_twin_score_ties": tie_queries,
        "locked_clean_first": {
            "k2_exposed": clean_first_exposure[2],
            "k5_exposed": clean_first_exposure[5],
        },
        "counterfactual_poison_first": {
            "k2_exposed": poison_first_exposure[2],
            "k5_exposed": poison_first_exposure[5],
        },
        "definition": (
            "Poison-first changes only deterministic ordering among equal BM25 scores; "
            "all scores, corpus contents, queries, and tokenization are unchanged."
        ),
    }
    return rows, sensitivity


def main() -> None:
    items = read_jsonl(ROOT / "benchmark/items/tier1_public.jsonl") + read_jsonl(
        ROOT / "benchmark/items/tier2_assets.jsonl"
    )
    items_by_id = {x["item_id"]: x for x in items}
    clean = read_jsonl(ROOT / "corpus/clean_documents.jsonl")
    poisons = read_jsonl(ROOT / "corpus/poison_variants.jsonl")

    dense = dense_audit(items_by_id, clean, poisons)
    bm25, bm25_tie_sensitivity = bm25_audit(items, clean, poisons)
    output = {
        "dense_reproduction": dense,
        "bm25_composition": bm25,
        "bm25_tie_sensitivity": bm25_tie_sensitivity,
    }

    out = ROOT / "results" / "upgrade_retrieval_audit.json"
    out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(out),
        "dense_rows_checked": dense["checked_generation_rows"],
        "rank_drift_count": dense["rank_drift_count"],
        "bm25_rows": len(bm25),
        "bm25_tie_sensitivity": bm25_tie_sensitivity,
    }, indent=2))
    if dense["rank_drift_count"]:
        raise SystemExit("Dense retrieval rank drift detected; stop final-upgrade interpretation.")


if __name__ == "__main__":
    main()
