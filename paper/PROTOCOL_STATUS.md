# Protocol status and deadline handling

## Locked design

The RQ1/RQ2/RQ3 design, metrics, analysis unit, model set, prompts, poison variants, retrieval settings, and primary endpoints were locked before any LLM generation result was observed.

## Public-source audit

All Tier-1 target values have been rechecked against the authoritative public sources or, for the two return-to-service values, the authoritative citation plus independent corroboration. See `benchmark/PUBLIC_SOURCE_AUDIT.md`.

## Independent engineer review

The external power-engineer review gate remains **pending**. No item is marked `engineer_reviewed=true` without explicit human approval.

Because the conference deadline is imminent, generation may be run on the committed, source-audited candidate benchmark before external review is returned. This is a schedule decision, not a claim that the human gate passed.

If external review changes any benchmark target, applicability condition, allowable interval, or poison value, every affected retrieval/generation result must be invalidated and rerun from the new frozen manifest.

The paper must not state that the benchmark was engineer-validated unless the review worksheet is completed and the corresponding item flags are updated.
