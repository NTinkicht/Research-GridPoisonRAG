# Stage-A retrieval calibration — design note

**Status:** design calibration only. These values were observed before LLM generation and before the human engineer-review/freeze gate. The final paper must rerun Stage A from the frozen benchmark.

The poison corpus was first corrected to use controlled lexical minimal pairs: the primary poison has the same wording as a clean support document with only the critical numeric value changed. This removes the earlier text-style confound.

## Observed retrieval exposure

At k=5:

| Condition | Tier 1 Poison@5 | Tier 2 Poison@5 | Overall Poison@5 |
|---|---:|---:|---:|
| 1 plain minimal-pair poison | 70.0% | 3.3% | 32.5% |
| 3 plain poison paraphrases/minimal pairs | 70.0% | 76.7% | 73.8% |
| 1 vendor-bulletin framed poison | 67.1% | 7.8% | 33.8% |

At k=10, the one-plain-poison condition reached 84.3% exposure on Tier 1 but 18.9% on Tier 2; the three-poison condition reached 84.3% and 98.9%, respectively.

## Design consequence

The one-poison natural-retrieval condition is retained because it is the lower-strength, realistic attack. However, it cannot support a clean Tier-1/Tier-2 conditional-adoption comparison: the Tier-2 exposed denominator is too small.

Before any generation result is observed, the study therefore locks:

- **RQ1:** natural retrieval and exposure/adoption decomposition for one and three poisons;
- **RQ2:** one-poison **forced exposure** in Stage B, with fixed five-passage context and poison first/last, so Tier-1 vs Tier-2 adoption is not confounded by retrieval;
- **RQ3:** the three-poison k=5 stress condition for D1/D2/D3 defense comparison, avoiding a retrieval floor.

This calibration decision must be disclosed if the paper describes how the final design was chosen.
