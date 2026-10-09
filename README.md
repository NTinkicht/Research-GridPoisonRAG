# Research-GridPoisonRAG

**Paper:** *Does the Assistant Check the Record? Knowledge-Base Poisoning and System-of-Record Validation in Utility Operations RAG*

GridPoisonRAG studies **answer integrity** in retrieval-augmented assistants used for utility-operations lookups. The threat is a low-trust writer who can add a small number of falsified documents to an indexed repository but cannot alter the authoritative system of record.

## Research questions

- **RQ1 — Exposure vs adoption:** How does targeted knowledge-base poisoning split into retrieval exposure and conditional adoption?
- **RQ2 — Parametric-prior split:** Does model prior knowledge protect public-standard facts more than asset-specific operational facts?
- **RQ3 — Record validation:** How much does system-of-record validation reduce out-of-range answers relative to prompt-level and isolate-then-aggregate defenses, and what false-flag cost does it introduce on legitimate conflicts?

## Benchmark design

The target benchmark is **GridPoison-100**:

- Tier 1: 35 public, citable normative lookups.
- Tier 2: 45 asset-specific lookups from a declared fictional utility register.
- Tier 3: 20 legitimate-conflict lookups used to measure false flags.
- ~400 short corpus documents including support documents, distractors and poison variants.

Every benchmark item stores an authoritative value, units, conditions, a source/record locator, an allowable range where meaningful, two query phrasings, and review status.

## Outcome taxonomy

Each generation trial receives exactly one label:

- **C**: correct committed value
- **A**: attacker value adopted
- **W**: other wrong committed value
- **F**: conflict correctly flagged without adopting the poison
- **R**: refusal / no committed value

The evaluation separates:

1. **Retrieval compromise**: poison appears in top-k.
2. **Generation compromise**: model commits to the poisoned value.
3. **Consequence violation**: committed value lies outside the benchmark's cited allowable range.

## Baselines and defenses

- **B0** closed book
- **B1** clean RAG
- **B2** poisoned vanilla RAG
- **D1** cautious/conflict-aware prompt
- **D2** isolate-then-aggregate evidence voting
- **D3** deterministic system-of-record validation

D3 is evaluated at imperfect record coverage rather than being treated as an oracle.

## Reproducibility rules

- Public-standard facts must have a public source and source locator.
- Asset-specific facts are explicitly fictional and cannot be presented as real utility data.
- No result may be described as proof of grid safety, security or resilience.
- The benchmark is frozen and hashed before model runs.
- Main runs use temperature 0; optional stochastic sensitivity runs are separate.
- Retrieval depth is a secondary factor, not a headline contribution.
- Do not reuse figures, prose or experimental framing from the prior healthcare-RAG access-control study.

## Status

The three-model experiment matrix is complete. The submission-facing analysis reports the pre-specified RQ3 comparison, natural-retrieval correctness/adoption outcomes, exact bounds for zero-event Stage-B cells, and the system-of-record scope assumptions. Tier 1 and Tier 3 public values are source-grounded; Tier 2 is fictional by construction. Historical planning gates remain in the repository for provenance but are not scientific submission requirements.


## Quick start

```bash
python -m pip install -e ".[dev]"
python scripts/validate_benchmark.py
pytest -q
```

Run the retrieval-only Stage A before any paid generation:

```bash
python scripts/run_stage_a.py --variant out_of_range_plain --poison-count 1 --out results/stage_a_plain_1.jsonl
python scripts/run_stage_a.py --variant out_of_range_plain --poison-count 3 --out results/stage_a_plain_3.jsonl
python scripts/run_stage_a.py --variant out_of_range_vendor_bulletin --poison-count 1 --out results/stage_a_bulletin_1.jsonl
```

The complete execution sequence is in [RUNBOOK.md](RUNBOOK.md).

## Current validation state

1. **Public-source audit:** Tier 1 source transcription and interpretation are documented in `benchmark/PUBLIC_SOURCE_AUDIT.md`.
2. **LLM domain audit:** all 100 items passed the documented automated technical-consistency review without a required target-value change. This does not set `engineer_reviewed=true`.
3. **Optional external review:** a human power-engineer review may strengthen a future benchmark release or journal extension; it is not required by the current benchmark-level answer-integrity claims.
4. **Clean-RAG gate:** Tier-2 clean-RAG CRR exceeded the locked 80% interpretation threshold for all three evaluated models.
5. **Claims:** report benchmark-level answer integrity and out-of-range commitments, never physical grid safety, security, or resilience.

## Repository map

- `benchmark/` — GridPoison-100 items, source catalog, fictional asset register, validation record and review worksheet.
- `corpus/` — 400 clean documents and controlled poison variants.
- `src/gridpoisonrag/` — retrieval, generation, grading, defenses, metrics and statistics.
- `scripts/` — validation, freezing, retrieval/generation runs, D3, analysis and adjudication tooling.
- `paper/` — IEEE manuscript and generated results, related-work positioning, methods lock and adjudication rubric.
- `.github/workflows/` — CI, retrieval-only Stage A, and manually triggered generation matrix.
