> **Status - 9 Oct 2026:** This is a historical project-planning artifact. The external engineer-review step below was an internal sequencing/quality-control gate, not a disciplinary requirement for the conference claims. It was not completed before the current submission. The paper therefore makes no engineer-validation or physical-safety claim; public benchmark facts are tied to cited sources and Tier 2 is fictional by declaration. The original planning text is retained below for provenance.

# Power-engineer review gate

The benchmark is deliberately **not** marked engineer-reviewed yet. This is the only external human gate that must not be fabricated or automated.

## Reviewer task

Review all 100 items in the attached CSV/JSONL benchmark with priority on:

- electrical plausibility of the 45 fictional asset records;
- correct interpretation of the public-source conditions and units;
- whether any query requires engineering judgment rather than a factual lookup;
- whether the allowable interval encoded for consequence grading is defensible;
- whether the unsafe poison direction is actually outside that interval;
- whether each Tier-3 conflict is genuinely legitimate and disambiguated by the query.

For each item, record **APPROVE**, **CHANGE**, or **REJECT**, with a short comment for non-approved items.

## Publication rule

Do not set `engineer_reviewed=true` unless a qualified electrical/power engineer has explicitly approved that item. Machine review, LLM review, or author self-review does not satisfy this field.

At least 60 approved items are required to pass the minimum submission gate; the target is all 100.

## Freeze rule

After review fixes, run:

```bash
python scripts/validate_benchmark.py
python scripts/build_corpus.py
python scripts/freeze_benchmark.py
```

Commit `benchmark/FROZEN_MANIFEST.json` before any final generation run.
