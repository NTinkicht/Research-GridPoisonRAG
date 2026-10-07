# Related-work positioning

## What is already known

The paper must explicitly concede the following rather than present them as novelty:

1. **RAG knowledge-base poisoning is established.** PoisonedRAG demonstrates that a small number of malicious texts can induce attacker-chosen answers in large corpora.
2. **Retrieval depth and retriever/database configuration affect poisoning exposure.** The 2026 Influence Factors study performs a broad factorial analysis; therefore any k sweep in this project is secondary.
3. **Models often adopt wrong retrieved evidence over correct priors.** ClashEval directly studies conflicts between parametric knowledge and retrieved content.
4. **Isolate-then-aggregate is an established defense family.** RobustRAG is the reference baseline for D2; D2 is not claimed as new.
5. **Evidence framing/metadata can change LLM behavior.** Wan et al. study what evidence models find convincing, and Chiang & Lee study publication time/source/appearance. Vendor-bulletin framing is therefore an attack condition, not a contribution.
6. **LLM risks in power systems are already discussed and experimentally explored.** Ruan et al. and Li et al. prevent any claim that this is the first LLM security work in power systems.

## Intended contribution

The attack is an instrument, not the contribution. The paper is positioned around three measurements:

- **Consequence grading:** generated numeric values are evaluated against a cited allowable interval or an explicit system-of-record maximum/minimum, separating mere wrong answers from out-of-range commitments.
- **Parametric-prior split:** public normative values are contrasted with fictional asset-specific values that cannot plausibly be memorized from pretraining.
- **System-of-record validation under imperfect coverage:** D3 is measured at 40%, 70% and 100% coverage and is penalized for false flags on legitimate conflicts.

## Relation to prior healthcare RAG work

Use a one-sentence disclosure in the paper:

> Our prior work asks whether an unauthorized user can obtain information they should not see; this study instead asks whether an authorized user receives a false operational value after a low-trust writer inserts content into the retrieval corpus.

Reused software infrastructure is disclosed but is not treated as a contribution. Do not reuse prior prose, figures, table layouts, or the structural-vs-heuristic defense framing.

## Claims to avoid

Do not claim:
- first LLM security study for smart grids or power systems;
- first RAG poisoning attack;
- k increasing attack exposure as a new finding;
- D3 as a new algorithmic idea;
- physical grid safety, secure deployment, or resilience;
- generality beyond the tested models, retriever and benchmark.
