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

Li et al., 2025 also matters for the generation-and-judging policy used here. The practical lesson from that preference-leakage line of work is that the same model family should not both author and judge the same synthesized task, because apparent agreement can be inflated by shared stylistic priors rather than true rubric fidelity. That is why this repo separates synthesis roles from judge-filter roles and preserves `preference_leakage_control` metadata in the preference-pair file.

The paper-to-design mapping is:

- **ORPO / SimPO**: small-budget preference optimization is a good fit for a lightweight Path B critic.
- **Prometheus 2**: evaluator models become more useful when the judgment rubric is explicit and narrow.
- **Li et al., 2025**: generation and judging should be family-separated to reduce preference leakage and avoid overstating model quality.

Alternative paths were considered and dismissed for evidence-based reasons:

- **Path A** was not selected because the Week 10 traces already show a functioning generator skeleton from enrichment through booking and CRM sync. The failure surface was inconsistent rule-following inside fluent drafts, not the inability to generate coherent outputs at all.
- **Path C** was not selected because the dominant Week 10 errors were localized output failures, such as over-claiming, tone drift, and handoff mistakes, rather than long-horizon trajectory failures requiring a step-level process reward model.

## Training Data

The train partition is converted into `training_data/path_b_preference_pairs.jsonl`. Each pair contains:

- the benchmark task input as prompt
- a chosen correction
- a rejected probe-triggered failure
- deterministic evaluator scores
- preference-leakage metadata

## Deployment Hypothesis

The critic should be used as a rejection-sampling or rollback layer. If the critic flags a draft below threshold, the production agent should rewrite or escalate instead of sending.
