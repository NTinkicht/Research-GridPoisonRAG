# Paper outline

## Working title

**Does the Assistant Check the Record? Knowledge-Base Poisoning and System-of-Record Validation in Utility Operations RAG**

Alternative: **One Bad Bulletin: Consequence-Graded Knowledge-Base Poisoning of Utility Operations Assistants**

## Abstract skeleton

1. Utility staff increasingly use document-grounded assistants for factual lookup, but indexed repositories may contain low-trust contributions.
2. Existing RAG-poisoning work establishes knowledge corruption; the unanswered question here is how corruption translates into **operationally meaningful numeric violations** and whether a separate structured record provides a useful guardrail.
3. Introduce GridPoison-100: 35 cited public facts, 45 asset-specific fictional records, and 20 legitimate-conflict cases.
4. Decompose attack success into retrieval exposure and conditional adoption; compare public-standard vs asset-specific facts.
5. Compare cautious prompting, isolate-then-aggregate, and system-of-record validation under imperfect coverage.
6. Report only measured results; no safety or resilience claim.

## 1. Introduction

- Utility-operation assistants are a plausible lookup interface, not an autonomous control loop.
- Low-trust writable repositories and spoofed bulletins create a write-path integrity threat.
- RAG poisoning itself is known; our question is consequence, prior knowledge, and independent-record checking.
- RQs:
  - RQ1 exposure vs adoption.
  - RQ2 public-standard vs asset-specific prior protection.
  - RQ3 record-check benefit, coverage ceiling and false flags.
- Contributions:
  1. threat model;
  2. GridPoison-100;
  3. consequence-graded decomposition;
  4. evaluation of D3 under partial coverage and benign conflicts.

## 2. Related Work

### 2.1 RAG poisoning and retrieval corruption
PoisonedRAG; Influence Factors; RobustRAG.

### 2.2 Conflicting evidence and parametric priors
ClashEval; Wan et al.; Chiang & Lee.

### 2.3 LLMs and security in power systems
Ruan et al.; Li et al.; additional NEECON-relevant work after verification.

### 2.4 Relation to our prior work
One explicit paragraph distinguishing confidentiality/access-control from integrity/write-path poisoning.

## 3. Threat Model

Attacker:
- authorized low-trust repository writer or source of a spoofed bulletin;
- may insert at most 1--3 documents;
- cannot edit/delete existing documents;
- cannot modify the system of record, EMS/SCADA or model weights;
- knows the target topic/asset, but not the exact query/retriever/corpus.

Goal: targeted integrity failure in a legitimate lookup.

Out of scope: confidentiality, prompt injection, availability attacks, model-weight poisoning, control-loop manipulation.

## 4. GridPoison-100

- 35 Tier-1 public authoritative facts.
- 45 Tier-2 fictional asset-specific facts.
- 20 Tier-3 legitimate conflicts.
- 400 clean documents + conditional poison variants.
- Two query phrasings per item.
- Engineer-review status and benchmark freeze hash.

## 5. Experimental Design

### Stage A: retrieval exposure
Report Poison@k for k={1,2,5,10}; poison count 1 and 3; natural and vendor-framed variants where applicable.

### Stage B: controlled adoption
Forced exposure on all 80 poisonable items using exactly five passages and one poison, with poison-first versus poison-last position control. This is the primary RQ2 design because it separates retrieval exposure from generation adoption.

### Generation conditions
B0, B1, B2, D1, D2, D3.

### Models
Three model families if time permits; two minimum after the deadline gate.

## 6. Metrics and Statistics

Outcome labels C/A/W/F/R.
Poison@k, ASR, CAR, CRR, CFR, SVR, BFFR.
Cluster bootstrap over items; paired McNemar tests with Holm correction where sample size supports them.
Automatic numeric grading; manual adjudication for conflict/refusal ambiguity.

## 7. Results

Primary:
1. Stage-B attacker-value adoption under forced exposure, Tier 1 vs Tier 2, reported separately for poison-first and poison-last contexts.
2. Delta-SVR D3_P3_70 vs D1_P3/D2_P3 under the three-poison stress condition, with D3_CONFLICT_70 BFFR.

Secondary:
- retrieval exposure;
- vendor framing;
- one vs three poisons;
- k=2 vs k=5;
- D3 coverage curve;
- position control.

## 8. Discussion

- what parametric knowledge does/does not buy;
- when a structured record is useful;
- coverage ceiling;
- legitimate disagreement and false flags;
- deployment implications limited to lookup assistants.

## 9. Limitations

- synthetic asset register;
- one dense retriever;
- limited models;
- non-adaptive primary attacker;
- no physical simulation;
- no real utility deployment;
- no causal claim about grid incidents.

## 10. Conclusion

State only empirical benchmark findings.
