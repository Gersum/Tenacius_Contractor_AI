# Datasheet: Tenacious-Bench v0.1

## 1. Motivation

**Telescopic view.** Tenacious-Bench v0.1 is a benchmark for Tenacious-style B2B sales-agent reliability. It exists because public tool-use and customer-support benchmarks do not grade whether an outreach agent stays honest about public hiring signals, avoids vendor-language drift, respects real bench capacity, and hands warm leads into scheduling safely.

The workflow domain is Tenacious Consulting and Outsourcing, but the dataset is intentionally synthetic and benchmark-oriented. It is meant to evaluate domain-specific judgment rather than expose private client data.

## 2. Composition

**Periscopic view.** The dataset contains `210` JSONL tasks. Each task includes:

- prospect metadata
- hiring-signal brief
- optional competitor-gap brief
- bench summary excerpt
- prior-thread context
- candidate output
- ground-truth fields
- rubric fields
- provenance metadata

### Counts by source mode

| Source mode | Count | Share |
|---|---:|---:|
| `trace_derived` | 63 | 30.0% |
| `programmatic` | 63 | 30.0% |
| `multi_llm_synthesis` | 53 | 25.2% |
| `hand_authored_adversarial` | 31 | 14.8% |

The target design was approximately `30 / 30 / 25 / 15`; the final counts match that target within integer rounding.

### Counts by partition

| Partition | Count | Share |
|---|---:|---:|
| `train` | 105 | 50.0% |
| `dev` | 63 | 30.0% |
| `held_out` | 42 | 20.0% |

### Counts by failure dimension

| Failure dimension | Count |
|---|---:|
| `tone_style_drift` | 30 |
| `hiring_signal_overclaiming` | 30 |
| `bench_overcommitment` | 30 |
| `competitor_gap_overclaiming` | 30 |
| `public_signal_reliability` | 30 |
| `scheduling_handoff_correctness` | 30 |
| `icp_misclassification` | 30 |

### Typical task by source mode

`trace_derived`: a compact reconstruction of a Week 10 conversation step, using real trace structure and a synthetic output candidate so the evaluator can test whether a grounded-looking draft still violates a Tenacious rule.

`programmatic`: a task expanded from the probe library or seeded sales material, where the public signal, bench excerpt, and failure trigger are systematically varied while the scoring fields remain machine-verifiable.

`multi_llm_synthesis`: a task whose wording is generated through the routed synthesis layer, with explicit model-route metadata and judge-filter metadata preserved in the task record.

`hand_authored_adversarial`: a deliberately sharp edge case written to expose failures generic B2B benchmarks would miss, such as weak-signal over-claiming or condescending competitor-gap framing.

## 3. Collection Process

Tasks were collected from four sources:

1. Week 10 traces and runtime artifacts.
2. Programmatic expansions of the Week 10 probe library and failure taxonomy.
3. Multi-LLM synthesis slots with route metadata and fallback deterministic stand-ins.
4. Hand-authored adversarial tasks targeting Tenacious-specific conversion failures.

Source provenance is preserved in each task through `metadata.source_refs`, `source_mode`, `synthesis_model`, `judge_model`, and `contamination_hash`.

## 4. Preprocessing / Cleaning / Labeling

**Microscopic view.** Each task is normalized into a common schema with:

- `required_claims`
- `forbidden_claims`
- `allowed_evidence_ids`
- `expected_action`
- deterministic check names
- optional reserved judge dimensions

Preprocessing strips the benchmark down to machine-checkable components. Public-signal details are retained only as synthetic or artifact-derived summaries. Held-out contamination hashes are generated during task construction. Preference-pair training data is created from the `train` partition only.

## 5. Uses

Intended uses:

- benchmark evaluation of Tenacious-specific sales-agent behavior
- training or evaluating a lightweight Path B critic
- ablation work comparing baseline, prompt-only, and critic-corrected outputs
- public demonstration of domain-specific benchmark design

Out-of-scope uses:

- measuring general customer-support quality
- claiming production conversion lift from benchmark scores alone
- ranking unrelated sales domains without adapting the rubric
- recovering real prospect identities or private commercial details

## 6. Distribution

Recommended release license: `CC-BY-4.0`.

Rationale: the benchmark is synthetic, reproducible, and intended for research-style reuse, but attribution should remain attached because the benchmark framing, schema design, and Tenacious-specific failure taxonomy are substantial authored work. Public release should include the dataset, `schema.json`, `scoring_evaluator.py`, contamination report, generation scripts, and this datasheet.

## 7. Maintenance

Current version: `v0.1`.

The dataset should evolve by:

- completing the human inter-rater cycle for the 30-task subset
- replacing deterministic multi-LLM stand-ins with real routed synthesis logs where budget allows
- expanding long multi-turn scheduling and handoff failures
- tightening the judge-filter layer after the first live Path B training run

Maintenance owner: the benchmark author or the next repo inheritor responsible for Week 11 artifacts. Any `v0.2` release should document changed counts, rubric revisions, and contamination-check deltas explicitly rather than silently regenerating tasks.
