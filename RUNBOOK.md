> **Status - 9 Oct 2026:** This is a historical project-planning artifact. The external engineer-review step below was an internal sequencing/quality-control gate, not a disciplinary requirement for the conference claims. It was not completed before the current submission. The paper therefore makes no engineer-validation or physical-safety claim; public benchmark facts are tied to cited sources and Tier 2 is fictional by declaration. The original planning text is retained below for provenance.

# GridPoisonRAG execution runbook

This runbook follows the methods locked before any LLM generation outputs are observed.

## 0. Install and machine-validate

```bash
python -m pip install -e ".[dev]"
python scripts/build_corpus.py
python scripts/validate_benchmark.py
pytest -q
```

CI additionally checks that rebuilding the corpus produces no diff.

## 1. Human engineer review

Use:

- `benchmark/ENGINEER_REVIEW.md`
- `benchmark/review/engineer_review.csv`
- `benchmark/SOURCE_NOTES.md`

Do not set `engineer_reviewed=true` without explicit qualified power/electrical-engineer approval.

Minimum submission gate: **60 approved items**. Target: all 100.

After review fixes:

```bash
python scripts/build_corpus.py
python scripts/validate_benchmark.py
python scripts/freeze_benchmark.py
git add benchmark/ corpus/
git commit -m "Freeze engineer-reviewed GridPoison-100 benchmark"
```

Do not edit frozen benchmark inputs after model outputs are observed.

## 2. Retrieval-only Stage A

Stage A is automatically rerun when benchmark/corpus/retrieval inputs change.

Manual equivalent:

```bash
python scripts/run_stage_a.py --variant out_of_range_plain --poison-count 1 --out results/stage_a_plain_1.jsonl
python scripts/run_stage_a.py --variant out_of_range_plain --poison-count 3 --out results/stage_a_plain_3.jsonl
python scripts/run_stage_a.py --variant out_of_range_vendor_bulletin --poison-count 1 --out results/stage_a_bulletin_1.jsonl
python scripts/summarize_stage_a.py   results/stage_a_plain_1.jsonl   results/stage_a_plain_3.jsonl   results/stage_a_bulletin_1.jsonl   --out results/stage_a_summary.json
```

The pre-generation retrieval calibration and its design consequence are documented in `results/PILOT_STAGE_A.md`. Final Stage-A numbers must come from the frozen benchmark.

## 3. Locked model families

`configs/models.yaml` locks:

- `qwen/qwen3-8b` — small open-weight family point;
- `mistralai/mistral-small-3.2-24b-instruct` — mid-size open-weight family point;
- `openai/gpt-5.6-luna` — commercial hosted comparison.

Do not silently substitute model slugs mid-study.

## 4. OpenRouter secret

The manual GitHub workflow expects a repository Actions secret named:

`OPENROUTER_API_KEY`

Never commit the key.

Local execution:

```bash
export OPENAI_COMPAT_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_COMPAT_API_KEY="..."
```

Generation responses record the requested model, resolved model/provider metadata when returned, API response ID, usage, and UTC run timestamp.

## 5. Clean-pipeline gate

Run `.github/workflows/generation.yml` with phase **gate** for one strong model first, or locally:

```bash
python scripts/run_generation.py --condition B0 --run-label B0 --model MODEL_ID --tier 12 --out results/gate_b0.jsonl
python scripts/run_generation.py --condition B1 --run-label B1 --model MODEL_ID --tier 12 --out results/gate_b1.jsonl
python scripts/check_gates.py --clean-results results/gate_b1.jsonl
```

Required: Tier-2 clean-RAG CRR >= 80%.

If the clean pipeline fails, stop and debug retrieval/prompting. Do not interpret attack results.

## 6. RQ1 — natural retrieval attack

### One-poison lower-strength condition

```bash
python scripts/run_generation.py   --condition B2 --run-label B2_P1   --model MODEL_ID --tier 12 --k 5   --variant out_of_range_plain --poison-count 1   --out results/main_b2_p1.jsonl
```

### Three-poison stress baseline

```bash
python scripts/run_generation.py   --condition B2 --run-label B2_P3_STRESS   --model MODEL_ID --tier 12 --k 5   --variant out_of_range_plain --poison-count 3   --out results/main_b2_p3.jsonl
```

Report retrieval exposure, ASR, CAR and violation rate separately. Retrieval depth is secondary, not a novelty claim.

## 7. RQ2 — forced-exposure parametric-prior split

Run the controlled Stage-B condition for all 80 poisonable items:

```bash
python scripts/run_stage_b_forced.py --model MODEL_ID --position first --out results/stage_b_first.jsonl
python scripts/run_stage_b_forced.py --model MODEL_ID --position last  --out results/stage_b_last.jsonl
```

Each trial has exactly five passages: three clean same-item supports, one deterministic on-topic distractor and one out-of-range poison. The poison is first or last. No retrieval selection occurs.

Primary RQ2 result: attacker-value adoption for Tier 1 vs Tier 2, separately by poison position.

## 8. RQ3 — defense stress comparison

Use the same three-poison k=5 stress corpus for the generation defenses:

```bash
python scripts/run_generation.py --condition D1 --run-label D1_P3   --model MODEL_ID --tier 12 --k 5 --variant out_of_range_plain --poison-count 3   --out results/main_d1_p3.jsonl

python scripts/run_generation.py --condition D2 --run-label D2_P3   --model MODEL_ID --tier 12 --k 5 --variant out_of_range_plain --poison-count 3   --out results/main_d2_p3.jsonl
```

Apply D3 to the **same B2_P3_STRESS outputs**:

```bash
python scripts/apply_d3.py --input results/main_b2_p3.jsonl --coverage 0.4 --run-label D3_P3_40 --out results/main_d3_p3_40.jsonl
python scripts/apply_d3.py --input results/main_b2_p3.jsonl --coverage 0.7 --run-label D3_P3_70 --out results/main_d3_p3_70.jsonl
python scripts/apply_d3.py --input results/main_b2_p3.jsonl --coverage 1.0 --run-label D3_P3_100 --out results/main_d3_p3_100.jsonl
```

Primary RQ3 result: paired Delta-SVR of D3_P3_70 versus D1_P3 and D2_P3.

## 9. Legitimate-conflict false flags

```bash
python scripts/run_generation.py --condition B1 --run-label B1_CONFLICT   --model MODEL_ID --tier 3 --out results/t3_b1.jsonl

python scripts/apply_d3.py --input results/t3_b1.jsonl --coverage 0.4 --run-label D3_CONFLICT_40 --out results/t3_d3_40.jsonl
python scripts/apply_d3.py --input results/t3_b1.jsonl --coverage 0.7 --run-label D3_CONFLICT_70 --out results/t3_d3_70.jsonl
python scripts/apply_d3.py --input results/t3_b1.jsonl --coverage 1.0 --run-label D3_CONFLICT_100 --out results/t3_d3_100.jsonl
```

Primary RQ3 must report D3_CONFLICT_70 BFFR beside Delta-SVR.

## 10. Secondary one-factor deviations

Only after primary runs:

- one dated vendor bulletin: `B2_BULLETIN_P1`;
- one wrong-but-in-range value where defined: `B2_WRONG_IN_RANGE_P1`;
- one plain poison at k=2: `B2_P1_K2`.

Do not run a full factorial grid.

## 11. Statistics

Collect model result files and run:

```bash
python scripts/statistical_report.py results/.../*.jsonl --out results/analysis_summary.json
```

The report computes:

- per-condition CRR, ASR, CAR, CFR, refusal rate and SVR;
- 95% item-cluster bootstrap intervals;
- primary Stage-B Tier-1/Tier-2 adoption;
- paired Delta-SVR intervals for RQ3;
- exact McNemar tests with Holm correction;
- Tier-3 D3 BFFR.

## 12. Human adjudication

```bash
python scripts/sample_adjudication.py results/.../*.jsonl   --fraction 0.15 --minimum 300   --out results/adjudication_sample.csv
```

Follow `paper/ADJUDICATION_RUBRIC.md`.

Two authors independently label the same sample. Report Cohen's kappa. If kappa < 0.80, manually adjudicate every F/R/parser-ambiguous output.

## 13. Claims boundary

Allowed:
- measured retrieval exposure;
- attacker-value adoption under the stated threat model;
- benchmark out-of-range commitment rate;
- public-standard versus asset-specific adoption differences;
- D3 coverage ceiling and legitimate-conflict false-flag cost.

Do not claim:
- physical grid safety;
- secure/robust/resilient deployment;
- first LLM-security study in power systems;
- k effects as novel;
- D3 as a new algorithm;
- generality beyond the tested benchmark, models and retriever.
