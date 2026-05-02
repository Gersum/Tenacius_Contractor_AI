---
license: cc-by-4.0
task_categories:
  - text-generation
  - text-classification
language:
  - en
pretty_name: Tenacious-Bench v0.1
size_categories:
  - n<1K
configs:
  - config_name: public_train_dev
    data_files:
      - split: train
        path: train/tasks.jsonl
      - split: dev
        path: dev/tasks.jsonl
dataset_info:
  features:
    - name: task_id
      dtype: string
    - name: partition
      dtype: string
    - name: source_mode
      dtype: string
    - name: difficulty
      dtype: string
    - name: failure_dimension
      dtype: string
    - name: input
      dtype: string
    - name: candidate_output
      dtype: string
    - name: ground_truth
      dtype: string
    - name: rubric
      dtype: string
    - name: metadata
      dtype: string
---

# Tenacious-Bench v0.1

Tenacious-Bench v0.1 is a benchmark for Tenacious-style B2B sales-agent reliability. It focuses on domain-specific failure modes that generic sales or agent benchmarks often miss: tone drift, hiring-signal over-claiming, bench over-commitment, competitor-gap over-claiming, public-signal reliability, scheduling handoff correctness, and ICP misclassification.

This dataset package is derived from:

- Week 10 traces and runtime artifacts
- probe-library expansions
- deterministic programmatic task generation
- hand-authored adversarial tasks

## Public release scope

This public dataset package is intended to expose the **train** and **dev** benchmark slices. The private held-out slice remains local by default in the repository publication flow so final evaluation can stay sealed.

Public counts:

- `train`: 105 tasks
- `dev`: 63 tasks
- public total: 168 tasks

Local-only by default:

- `held_out`: 42 tasks

## Source-mode mix

Full benchmark target mix:

- trace-derived: approximately 30%
- programmatic: approximately 30%
- multi-LLM synthesis: approximately 25%
- hand-authored adversarial: approximately 15%

## Files

- `train/tasks.jsonl`
- `dev/tasks.jsonl`
- `examples/`
- `contamination_check.json`

Supporting docs published alongside the dataset from the repo-level script:

- `datasheet.md`
- `methodology.md`
- `audit_memo.md`
- `evidence_graph.json`

## Rebuild locally

```bash
python3 generation_scripts/build_tenacious_bench.py
```

## Score locally

```bash
python3 -m eval.tenacious_bench.scoring_evaluator tenacious_bench_v0_1/dev/tasks.jsonl
```

## Contamination check

```bash
python3 -m eval.tenacious_bench.contamination_check
```

## Quickstart

```python
import json
from pathlib import Path

rows = []
with Path("tenacious_bench_v0_1/dev/tasks.jsonl").open() as f:
    for line in f:
        rows.append(json.loads(line))

print(rows[0]["task_id"], rows[0]["failure_dimension"])
print(rows[0]["candidate_output"])
```

## Citation

If you use this dataset, cite the repository documentation and datasheet bundled with the release.
