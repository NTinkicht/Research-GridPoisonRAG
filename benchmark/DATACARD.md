# GridPoison-100 data card

## Purpose

GridPoison-100 is a controlled benchmark for studying **numeric answer integrity** in document-grounded utility-operations lookup assistants under targeted knowledge-base poisoning. It is not a grid-control dataset and is not intended to support claims about physical power-system safety.

## Composition

- 35 Tier-1 public-source normative lookup items.
- 45 Tier-2 asset-specific lookup items from the explicitly fictional Northbridge Utility register.
- 20 Tier-3 legitimate-conflict items.
- 400 clean short documents: support documents, legitimate-conflict documents, and on-topic distractors.
- Controlled poison variants for the 80 poisonable Tier-1/Tier-2 items.

## Sources

Tier 1 is constructed from publicly accessible Massachusetts DER settings material, OSHA 29 CFR 1910.269 material, and NERC PRC-024-3. Source URLs and source locators are stored item by item.

Tier 2 is synthetic by design. No asset ID, rating, limit, or setting in the Northbridge Utility register describes a real utility.

Tier 3 intentionally pairs legitimate values that differ because of jurisdiction or interconnection context. The query names the applicable context.

## Poison construction

Primary poison variants are factual assertions and contain no instructions to the model. The main condition changes the critical numeric value while retaining the item's target context. Three-poison trials use distinct paraphrases rather than duplicated text; one paraphrase inherits the directive wording of the clean training-card template while changing only the value. A dated vendor-bulletin framing variant is secondary.

## Intended use

Research on:
- retrieval exposure to targeted poisoned documents;
- conditional adoption of attacker values;
- public-standard versus asset-specific parametric-prior effects;
- numeric consequence grading;
- incomplete system-of-record validation and legitimate-conflict false flags.

## Non-intended use

Do not use the benchmark:
- as operational guidance;
- as a source of real utility settings;
- to infer physical consequences of an LLM answer;
- to claim a deployed system is secure, safe, robust, or resilient.

## Validation status

The machine-readable files pass schema and count validation. Tier-1 and Tier-3 public values retain source URLs/locators and are source-audited; Tier-2 values are fictional by construction. The `engineer_reviewed` field is reserved strictly for explicit human engineer sign-off and remains false; the current paper does not rely on or claim that status.

## Reproducibility

Git history preserves the benchmark/corpus state used for generation. A pre-generation SHA-256 manifest was planned but not committed; this is documented as provenance rather than retroactively described as preregistration. The two query phrasings of one item are repeated measures, not independent benchmark samples.

## Known overlaps and collisions

Some controlled values overlap by construction. T1-003/T3-001 and T1-004/T3-003 reuse the same Massachusetts undervoltage facts in different benchmark roles. A small number of poison values equal another item's legitimate value. Grading is item-scoped, so these collisions do not change adoption labels.
