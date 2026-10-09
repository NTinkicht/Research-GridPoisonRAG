# Known analysis and reporting limitations - 2026-10-09

This file records implementation details that are relevant to reproducibility but are not all scientific endpoints.

- The raw grader retains F/R/W parser labels for diagnostics. The F/R split depends on narrow regexes and was not human-adjudicated. The submission therefore pools every response without a parsed numeric VALUE as non-commitment and does not report CFR or refusal-rate claims.
- In the wrong-but-in-range ablation, raw label A still refers to the primary out-of-range poison. Direct wrong-in-range adoption is therefore recomputed explicitly from the committed value and each item's poison_value_wrong_in_range.
- GPT-5.6 Luna produced 50 empty responses under the 256-token output cap: 41 in B0, one each in the bulletin, k=2 and B2_P1 runs, two in D1, and four in Stage-B-first. Empty outputs are non-correct and contain no numeric commitment.
- OpenRouter provider routing was not pinned. Requested/resolved model identifiers, provider metadata when returned, response IDs, token usage and timestamps are preserved in raw result rows.
- A pre-generation SHA-256 manifest was planned but was not committed. Git commit history is the provenance record for the immutable benchmark/corpus used by the completed runs; no later manifest is presented as a preregistration artifact.
- D3 receives the benchmark item ID as the record key. Query-to-record entity linking is therefore outside scope, and D3 should be interpreted as an upper-bound structured-record check rather than a complete deployed defense.
