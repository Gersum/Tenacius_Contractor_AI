# Tenacious-Bench: A Sales-Agent Benchmark for Public-Signal Grounding, Tone, and Handoff Reliability

Tenacious-Bench is a reproducible benchmark for a narrow but commercially important problem: whether a sales agent can use public signals, preserve Tenacious-style outreach quality, and hand a warm lead into scheduling without creating trust-destroying mistakes. The dataset packages that problem into a reviewer-friendly evaluation surface with deterministic scoring, trace-backed evidence, and a published dataset at [Hugging Face](https://huggingface.co/datasets/recordabebe/tenacious_bench_v0_1). The goal is not to replace general agent benchmarks, but to measure the failure modes those public benchmarks routinely miss.

## Why this benchmark exists

General tool-use and agent benchmarks can tell you whether a model completed a sequence of actions. They are much weaker at telling you whether the model softened a weak hiring signal, stayed inside real delivery capacity, sounded like a high-context engineering partner rather than a commodity staffing vendor, or proposed a scheduling handoff that was actually timezone-safe.

That distinction matters in Tenacious-style sales work. A reply can be fluent and still be commercially wrong. A message can be persuasive and still over-claim from thin public evidence. A meeting can be booked and still be a failure if the promise behind it was not supportable. Tenacious-Bench was built to make those failure modes visible and measurable.

## What we built

The project has two linked layers.

The first is a thin-slice conversion engine that performs public-signal enrichment, competitor-gap briefing, email-first outreach, reply qualification, Cal.com booking with fallback behavior, and HubSpot contact snapshotting. That layer exists so the benchmark is grounded in a real workflow rather than an abstract task collection.

The second is Tenacious-Bench v0.1 itself: a benchmark scaffold with 210 tasks split into train, dev, and held-out partitions. The dataset includes deterministic scoring code, contamination checks, committed task metadata, and an evidence graph that maps headline claims back to trace or evaluation artifacts. The dataset is published here:

- [recordabebe/tenacious_bench_v0_1](https://huggingface.co/datasets/recordabebe/tenacious_bench_v0_1)

The benchmark covers seven Tenacious-specific failure dimensions:

- hiring-signal over-claiming
- public-signal reliability
- bench over-commitment
- tone and style drift
- scheduling handoff correctness
- competitor-gap over-claiming
- ICP misclassification

Those dimensions came from the Week 10 probe library and trace evidence, not from generic benchmark categories.

## Evaluation highlights

From the imported Week 10 dev evidence, the baseline system recorded:

- dev `pass@1`: `0.7267` with `95% CI [0.6504, 0.7917]`
- small reproduction check (`15` trajectories): `0.8667` with `95% CI [0.6212, 0.9626]`
- p50 latency: about `106s`
- p95 latency: about `552s`
- average agent cost: about `$0.0199` per simulation

For the benchmark package itself, the committed held-out ablation scaffold reports a positive deterministic Delta A:

- baseline average score: `0.6190`
- critic-correction path average score: `0.8571`
- lift: `+0.2381`
- paired bootstrap `p = 0.031`
- reported `95% CI [0.08, 0.18]`

Those numbers matter because they show that the benchmark can detect quality deltas on the held-out slice rather than only serve as a task archive.

## The honest Path B result

I chose **Path B**, a lightweight preference critic, because the Week 10 traces suggested the main problem was inconsistency rather than total generation failure. The agent could already move from enrichment to outreach, qualification, booking, and CRM sync, but it could still violate tone, grounding, or capacity constraints in locally fluent ways.

A real ORPO run was completed on Google Colab T4 using a small Qwen backbone. That closes the “training stack never exercised” gap. But the current result does **not** justify a deployment claim yet.

The reason is simple: the first held-out smoke test on task `tb-0169` showed no lift. The baseline scored `0.2`, and the trained adapter also scored `0.2`. In practice, the learned adapter still drifted into explanation or prompt-echo behavior when asked to rewrite weak outreach. So the current benchmark package is strong, the training execution is real, and the learned component is still not ready to replace the Week 10 generator or act as a trusted production critic.

That negative result is still useful. It means the benchmark is doing its job: it can distinguish between a technically successful training run and a commercially useful model improvement.

## What reviewers should inspect first

If you want to understand the project quickly, start with these:

1. The published dataset: [recordabebe/tenacious_bench_v0_1](https://huggingface.co/datasets/recordabebe/tenacious_bench_v0_1)
2. The evidence graph in the repository, which maps numeric claims to source artifacts
3. The methodology and datasheet, which explain the partitioning protocol, contamination checks, and rubric structure
4. The inter-rater packet and agreement matrix, which show how rubric consistency was checked on a committed 30-task subset

The benchmark was designed so a skeptical reviewer can inspect the dataset, scoring logic, and narrative claims without needing to trust a hidden notebook or a one-off demo.

## What comes next

Tenacious-Bench v0.1 is a strong benchmark scaffold, not the final word on sales-agent evaluation.

The next version should add at least four things the current benchmark still under-captures:

- cross-account repetition risk across campaigns
- downstream meeting quality, not just outreach correctness
- quality of human escalation packages
- longer multi-turn recovery after skeptical replies or scheduling failures

The training side also needs another honest iteration. The next Path B step is not “declare victory”; it is to improve the preference-pair format, evaluate the learned component more broadly on held-out tasks, and keep comparing it against a prompt-only baseline on the same backbone.

That is the main takeaway from this project: domain-specific agent evaluation is valuable precisely because it can tell you when a system is not ready, even after a benchmark, a dataset, and a training run all exist.
