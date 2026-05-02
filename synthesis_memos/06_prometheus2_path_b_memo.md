# Synthesis Memo: Prometheus-Style Evaluator Specialization

## Design Choice I Disagree With

I disagree with the design instinct to make the specialized evaluator do too much of the benchmark's conceptual work. A stronger evaluator is useful, but for Tenacious-Bench it should not be the thing that defines the task.

## Why Repo Evidence Pushes Back

The repo's strongest evaluator behavior today comes from explicit structure, not evaluator cleverness:

- required claims are named
- forbidden claims are named
- expected actions are named
- dimension-specific guardrails are named

That structure is why the deterministic evaluator can discriminate obvious failures like:

- vendor-generic tone drift
- over-claiming weak public signals
- unsafe bench promises
- timezone-handling mistakes

The current missing work also proves the same point from the other direction. Inter-rater agreement is still incomplete. That means evaluator specialization would be premature if it were asked to compensate for unresolved rubric ambiguity. We would be specializing a judge against a target that is not fully human-validated yet.

## Alternative Choice I Defend

For Path B in this repo, evaluator specialization should come after three conditions:

1. the benchmark rubric is explicit
2. inter-rater agreement is completed
3. deterministic checks already cover the non-ambiguous parts

Only then should a Prometheus-style evaluator become a serious substitute for residual human judgment. Otherwise it risks learning our benchmark shortcuts rather than our benchmark intent.

## Bottom Line

I agree with the value of evaluator specialization, but I disagree with letting the evaluator stand in for unfinished rubric work. Tenacious-Bench should first become explicit and human-legible, and only then become more model-judged.
