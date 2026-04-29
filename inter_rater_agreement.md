# Inter-Rater Agreement

The current v0.1 repository includes a scaffolded 30-task relabel plan rather than a completed 24-hour human relabel cycle.

## Protocol

1. Sample 30 tasks across all seven failure dimensions.
2. Label each task for required-claim correctness, forbidden-claim absence, expected action, and dimension-specific guardrail.
3. Wait 24 hours.
4. Relabel the same 30 tasks without looking at the first labels.
5. Require at least 80% agreement per major rubric dimension.

## Current Deterministic Proxy

The deterministic evaluator was run on three committed example tasks and the generated held-out scaffold. This is not a replacement for human relabeling, but it verifies that the rubric can be applied mechanically.

| Dimension | Agreement target | Current status |
|---|---:|---|
| Required claims | 80% | pending human relabel |
| Forbidden claims | 80% | pending human relabel |
| Expected action | 80% | pending human relabel |
| Dimension guardrail | 80% | pending human relabel |

## Revision Rule

If any dimension falls below 80%, revise the relevant rubric text in `eval/tenacious_bench/schema.json` and regenerate the affected tasks before training.

