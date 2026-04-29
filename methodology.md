# Tenacious-Bench v0.1 Methodology

## Path Declaration

This repository uses **Path B: lightweight preference critic**.

The choice is evidence-driven. Week 10 traces `tr_d836ebb13a91`, `tr_fe2b1396e43c`, and `tr_4c1c7ea77e33` show that the system can already gather inputs, compose outreach, send email, and qualify replies. Traces `tr_01246c6c745b` and `tr_798431a02fa8` extend that same point through booking and CRM sync. That pattern argues against spending Week 11 first on a stronger generator. The more pressing problem is inconsistency: fluent outputs can still violate tone, evidence-restraint, bench-capacity, or scheduling rules. That is the failure profile Path B is designed to catch.

## Reading-Based Justification

The methodology follows two ideas from the Week 11 reading set:

- from **ORPO / SimPO**, preference-style optimization is a practical fit for small-budget correction layers, which is why the repo prepares chosen-versus-rejected pairs rather than a full reward-model stack
- from the **LLM-as-a-Judge survey**, judge systems are most trustworthy when the rubric is explicit, which is why Tenacious-Bench makes deterministic checks first and reserves model judgment for narrower residual dimensions

In other words, Week 10 evidence says the generator skeleton exists, while the reading suggests the highest-ROI intervention is a critic trained on explicit preference pairs.

## Partitioning Protocol

Tenacious-Bench v0.1 contains `210` tasks split as:

- `105 train` tasks (`50%`)
- `63 dev` tasks (`30%`)
- `42 held_out` tasks (`20%`)

The split is fixed at generation time. Stratification serves failure-mode coverage rather than chronology: every failure dimension appears 30 times overall, and source-mode counts are balanced near the target `30 / 30 / 25 / 15` mix. The held-out partition is not a random leftovers bucket. It is shaped to keep coverage across the same seven failure dimensions while preserving enough adversarial examples to test whether the critic generalizes beyond template corrections.

Training code is expected to read only the `train` partition and the preference-pair file derived from it. The `dev` split exists for visible iteration. The `held_out` split is reserved for sealed comparison and final reporting.

## Model Route Policy

- `trace_derived`: no LLM; tasks are built from local Week 10 traces and runtime artifacts
- `programmatic`: no LLM; tasks are built from templates, probes, and seeded Tenacious materials
- `multi_llm_synthesis`: routed generation path using OpenRouter only when explicitly enabled; the committed seed remains reproducible without API calls
- `judge_filter`: deterministic evaluator first, with eval-tier judgment reserved for calibration samples rather than the full dataset

This separation is meant to reduce preference leakage. The same model family should not be both the synthesis author and the evaluator for the same task.

## Contamination-Check Results

Three contamination checks are run before held-out use:

1. `8-gram overlap` between train and held-out prompt surfaces  
   Result: `0` flagged pairs. No held-out tasks required rewrite or drop.

2. `token-cosine similarity` as the local stand-in for an embedding-similarity gate, with threshold `< 0.85`  
   Result: maximum similarity was `0.0`, so `0` task pairs crossed the threshold and no rewrites were needed.

3. `time-shift verification` on held-out source references  
   Result: `0` held-out tasks were flagged for generic-placeholder or bad time-shift references.

Final pass status: **passed**. The current committed report is `tenacious_bench_v0_1/contamination_check.json`.

## Cost Tracking

The committed scaffold cost is still `$0.00` in external API and compute spend because generation, scoring, and contamination checks all run locally. Future OpenRouter synthesis, Colab, or RunPod training runs should append timestamped entries to `cost_log.md`, including provider, purpose, and exact spend.
