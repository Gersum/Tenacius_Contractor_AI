# Methodology Rationale: Path B Critic

## Choice

The selected Week 11 path is **Path B: preference-tuned critic**. The critic is designed to sit in front of Week 10 output acceptance and reject messages that violate Tenacious-specific rules.

## Week 10 Evidence

The workflow traces show the agent can complete the main path from enrichment to booking:

- `tr_d836ebb13a91`: compose initial outreach
- `tr_fe2b1396e43c`: send email
- `tr_4c1c7ea77e33`: qualify reply
- `tr_01246c6c745b`: book Cal.com meeting
- `tr_798431a02fa8`: sync HubSpot-shaped record

That points away from training a new generator first. The more useful intervention is a critic that catches when a locally fluent output over-claims, uses banned tone, ignores bench capacity, or mishandles scheduling.

## Paper Basis

Direct Preference Optimization establishes preference-pair training as a practical alternative to reward-model-heavy RLHF. ORPO and SimPO are attractive here because they reduce reference-model overhead and fit the challenge's small compute envelope. Prometheus 2 supports the idea that small evaluator models can be specialized for domain-specific judgment when the rubric is explicit.

## Training Data

The train partition is converted into `training_data/path_b_preference_pairs.jsonl`. Each pair contains:

- the benchmark task input as prompt
- a chosen correction
- a rejected probe-triggered failure
- deterministic evaluator scores
- preference-leakage metadata

## Deployment Hypothesis

The critic should be used as a rejection-sampling or rollback layer. If the critic flags a draft below threshold, the production agent should rewrite or escalate instead of sending.

