## Community Engagement Post Draft

### Suggested target

GitHub issue or discussion on the `τ²-Bench` repository.

### Suggested title

`Tenacious-specific benchmark gap: public-signal grounding, tone drift, and scheduling handoff failures`

### Paste-ready post

Hi maintainers — sharing a focused benchmark-gap report from a Tenacious-style sales-agent evaluation workflow.

I’ve been exploring a benchmark slice for sales-agent reliability where outputs can look fluent but still violate policy and business constraints. I think this can complement `τ²-Bench` by adding a narrower stress test for high-risk outbound messaging behavior.

## Problem Context

In my Week 10 traces, strong general agent behavior did not always translate to safe sales behavior. The repeated failure patterns were:

- overconfident claims from weak public signals
- bench-capacity over-commitment beyond what delivery could actually support
- tone and style drift into commodity-vendor language
- scheduling handoff errors that still “complete” the workflow but damage conversion quality
- competitor-gap claims that overstate what public evidence actually supports

## Approach

I built **Tenacious-Bench v0.1** with:

- mixed task construction across trace-derived, programmatic, multi-LLM synthesis, and adversarial modes
- machine-verifiable rubric constraints focused on grounding, honesty, tone, and handoff correctness
- train/dev/held-out partitioning with contamination checks
- a Path B preference-critic experiment to test whether a lightweight learned intervention could improve reliability on Tenacious-specific slices

## Key Findings

The benchmark package itself is now published and reproducible. Tenacious-Bench v0.1 contains `210` tasks across train/dev/held-out partitions and scores seven failure dimensions:

- hiring-signal over-claiming
- public-signal reliability
- bench over-commitment
- tone/style drift
- scheduling handoff correctness
- competitor-gap over-claiming
- ICP misclassification

On the committed held-out ablation scaffold (`n=42`), the deterministic critic-correction path reports:

- baseline average score: `0.6190`
- critic-correction average score: `0.8571`
- Delta A: `+0.2381`
- reported `95% CI [0.08, 0.18]`
- paired bootstrap `p = 0.031`

One honest note: the learned Path B ORPO run was a real training execution, but the first held-out smoke test on task `tb-0169` showed no lift (`0.2 -> 0.2`). So the benchmark package is stronger than the current trained-model result, and I do **not** yet treat the learned component as deployment-ready.

## Interpretation

My main takeaway is that public benchmarks can confirm workflow competence, but they often miss the narrower policy-sensitive failure surface that matters in sales outreach:

- safe use of weak public signals
- bounded claims about delivery capacity
- company-specific tone compliance
- conversion-safe scheduling handoffs

That seems like a useful complementary stress-test area rather than a replacement for broader agent benchmarks.

## Collaboration Proposal

If useful, I’d be happy to contribute:

- a compact “sales-policy reliability” subset for discussion
- a failure-dimension mapping from probes to rubric dimensions
- a minimal protocol proposal for evaluating policy-sensitive outbound responses

## References

- Dataset: https://huggingface.co/datasets/recordabebe/tenacious_bench_v0_1
- Technical write-up: https://medium.com/@recordabebe2/tenacious-bench-a-sales-agent-benchmark-for-public-signal-grounding-tone-and-handoff-reliability-b4feef96b2f3

### After posting

Replace the placeholder community-engagement link in [README.md](/Users/gersumasfaw/Downloads/week_10/README.md:1) with the real GitHub issue or discussion URL.
