# NEECON 2026 submission compliance gate

Checked against the NEECON 2026 Author Resources page on 2026-10-10.

Official source: https://neecon.org/author-resources/

## Verified requirements

- Paper length: 4-6 pages.
- Format: standard IEEE two-column.
- Submission platform: EDAS.
- The paper should describe the contribution and results and frame the work in related state of the art.
- Camera-ready PDF must be validated with IEEE PDF eXpress.
- Conference PDF eXpress ID: 71729X.
- The venue states that generative-AI tool use must be disclosed in the manuscript.

## Current repository status

- Six-page limit is enforced in the paper-build workflow.
- Manuscript source constraints are enforced in CI.
- Current owner instruction intentionally forbids a standalone Limitations section and a Generative AI Use Disclosure section and forbids any related disclosure text in the manuscript.
- Therefore the AI-disclosure requirement is an explicit owner-policy conflict. Automation must not silently insert disclosure text. Owner approval is required before changing this constraint.
- No double-blind/anonymization requirement is stated on the current NEECON Author Resources page.

## Final submission gates

1. Latest CI green.
2. Latest PDF build green and page-count gate passes.
3. PDF visually inspected.
4. IEEE PDF eXpress validation passes.
5. Owner resolves the venue AI-disclosure conflict before final submission.
