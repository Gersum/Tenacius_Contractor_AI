# Inter-Rater Packet

This directory contains the committed 30-task subset for the required two-pass inter-rater agreement run.

## Contents

- [sample_tasks.jsonl](sample_tasks.jsonl): exact dev-split task packet to label
- [label_sheet.csv](label_sheet.csv): fillable pass-1 / pass-2 labeling sheet

## Sampling policy

- Partition: `dev` only, to preserve the sealed held-out split
- Per dimension: all `3` programmatic tasks plus `1` multi-LLM synthesis task
- Extra synthesis tasks added for `tone_style_drift` and `scheduling_handoff_correctness` to reach `30` rows total

## Composition

- `tone_style_drift`: 5 tasks
- `hiring_signal_overclaiming`: 4 tasks
- `bench_overcommitment`: 4 tasks
- `competitor_gap_overclaiming`: 4 tasks
- `public_signal_reliability`: 4 tasks
- `scheduling_handoff_correctness`: 5 tasks
- `icp_misclassification`: 4 tasks

- `programmatic`: 21 tasks
- `multi_llm_synthesis`: 9 tasks

## Labeling rule

Fill pass 1 first, wait 24 hours, then fill pass 2 without looking back at pass 1.
