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

## Inter-Rater Agreement Matrix

The 30-task two-pass relabel cycle is now complete on the committed `dev`-split packet. The exact subset lives in [inter_rater/sample_tasks.jsonl](/Users/gersumasfaw/Downloads/week_10/inter_rater/sample_tasks.jsonl:1), the completed sheet is [inter_rater/label_sheet.csv](/Users/gersumasfaw/Downloads/week_10/inter_rater/label_sheet.csv:1), and the computed matrix is saved in [inter_rater/agreement_results.md](/Users/gersumasfaw/Downloads/week_10/inter_rater/agreement_results.md:1).

Sampling policy for the committed packet:

- partition: `dev` only, to preserve the sealed held-out split
- coverage: all seven failure dimensions represented
- source modes: `21 programmatic`, `9 multi_llm_synthesis`
- total: `30` tasks

| Rubric dimension | Agreement % | Threshold | Current status | Next action |
|---|---:|---:|---|---|
| Required claims | 100.0% | 80% | pass | no revision needed |
| Forbidden claims | 100.0% | 80% | pass | no revision needed |
| Expected action | 100.0% | 80% | pass | no revision needed |
| Dimension guardrail | 100.0% | 80% | pass | no revision needed |

Revision rule: if any dimension lands below `80%`, revise the rubric language, document the diagnosis, and rerun the affected subset before freezing the benchmark. The current committed run cleared all four dimensions on the first recorded pass, so no revision loop was triggered.

## Cost Tracking

The committed scaffold cost is still `$0.00` in external API and compute spend because generation, scoring, and contamination checks all run locally. Future OpenRouter synthesis, Colab, or RunPod training runs should append timestamped entries to `cost_log.md`, including provider, purpose, and exact spend.

## Live Training Execution Status

A first real Path B training run has now been completed outside the local repo on **Google Colab T4**:

- algorithm: `ORPO`
- backbone: `Qwen/Qwen2.5-0.5B-Instruct`
- train rows: `94`
- eval rows: `11`
- global steps: `24`
- wall-clock runtime: `97.7594` seconds
- final train loss: `1.5820321440696716`

This closes the “training stack not yet exercised” gap, but it does **not** yet justify a deployment claim. A held-out smoke test on task `tb-0169` (`tone_style_drift`) produced no measurable improvement:

- baseline score: `0.2`
- trained-adapter score: `0.2`

Interpretation: the first ORPO run was a **technical training success** but a **weak held-out generation result**. The repo should therefore treat this adapter as experimental and non-deployment-ready until a broader held-out pass shows positive lift.
