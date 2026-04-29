# Judge Filter Prompt

You are scoring a synthetic benchmark task draft before it is admitted into the multi-LLM slice.

Score each dimension on a bounded integer scale from `1` to `5`:

- `input_coherence`
  - `1`: task fields contradict each other or the candidate ignores the task
  - `3`: task is mostly coherent but one field is weakly aligned
  - `5`: task and candidate are tightly aligned
- `ground_truth_verifiability`
  - `1`: required claims or expected action cannot be checked from the task
  - `3`: some parts are checkable but one rule is too loose
  - `5`: required claims, forbidden claims, and action are all auditable
- `rubric_clarity`
  - `1`: the failure mode is ambiguous
  - `3`: the intended failure is visible but not sharply isolated
  - `5`: the intended failure mode is explicit and discriminative

Admission rule:

- accept only if all three dimensions are `>= 4`
- reject near-duplicates even if the scores clear the threshold
- the same model family must not both generate and judge the same task
