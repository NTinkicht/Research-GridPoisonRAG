# Claude Hostile Review Round 2 Resolution - 2026-10-10

Reviewed manuscript: six-page PDF with title "Silent Adoption or Non-Commitment? Knowledge-Base Poisoning and Record-Scope Costs in Utility-Operations RAG".

Claude Round 2 verdict:
- WEAK ACCEPT, confidence 3/5.
- Acceptance estimate: 65%.
- Submission readiness: SUBMIT AFTER MINOR EDITS.
- Critical scientific issues: NONE.
- Numerical audit: PASS.
- Technical correctness, methodological rigor, and statistical rigor: 8/10 each.
- Overall paper quality: 7/10.
- No new experiment requested; remaining fixes were text/analysis-presentation items.

## Implemented from Round 2

1. Table V is now cited and interpreted in prose. The manuscript explicitly notes the 22 attacker versus 23 correct Mistral transitions from base non-commitments, and Luna's 26 correct versus 6 attacker transitions plus 12 N-to-N transitions.
2. D1 is clarified as receiving no separate structured-record content or record key; it sees only retrieved passages.
3. The twin audit is completed using existing logs: at Tier-1 k=5, all 47 twin-present exposed trials had zero adoption and both twin-absent trials adopted in every original model. At k=2, all 17 Tier-1 clean-evidence exposures contained the paired twin and had zero adoption; all 9 twin-absent exposures adopted. This remains explicitly labeled as a post-outcome consistency check.
4. The primary commit collapse rule is now explicit: an item is positive if any exposed phrasing adopts. The strict sensitivity requires both phrasings to be exposed and both to adopt; one-exposed-phrasing items count negative.
5. Intro terminology changed from "prompt-mediated" to "prompt-dependent" and from "two generic defenses" to "two prompt/aggregation baselines".
6. Closed-book Tier-1 counts are labeled by model.
7. Table IV now says its columns are nominal coverage and gives realized Tier-3 coverage (6/20, 14/20, 20/20).
8. The inaccurate "Table IV makes the construction explicit" wording is replaced by "reports the resulting rates".
9. RQ2 wording was softened from causal "because" language to an inconclusive floor "consistent with" the Stage-C twin result.
10. Consequence-mapping wording was de-duplicated and its electrical-component referent clarified.
11. The abstract was shortened from 263 words to approximately 221 words while preserving all primary findings and caveats.

## Verified after edits

- CI: PASS.
- Analyze Final Upgrade workflow: PASS.
- Build Paper PDF workflow: PASS.
- Submission page gate: exactly 6 pages.
- Rendered visual inspection: all six pages checked; no clipping or overlap observed.
- No new experimental data were introduced.
- No Unicode em dash was introduced.

## Remaining non-scientific submission gates

- The current manuscript still contains author names and the public repository URL; final anonymization depends on the venue's actual review policy.
- If an abstract/title was already registered, the owner should confirm whether the revised title can still be changed.
- The venue AI-use disclosure issue remains intentionally unresolved because the owner's standing instruction forbids adding that disclosure to the manuscript. Automation must not silently override that instruction.
