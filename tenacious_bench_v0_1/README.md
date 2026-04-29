# Tenacious-Bench v0.1

Tenacious-Bench v0.1 is a 210-task benchmark for Tenacious-style B2B sales-agent reliability. It is built from Week 10 traces, runtime artifacts, probe definitions, and deterministic task templates.

## Partitions

- `train/tasks.jsonl`: 105 tasks
- `dev/tasks.jsonl`: 63 tasks
- `held_out/tasks.jsonl`: 42 tasks

## Rebuild

```bash
python3 generation_scripts/build_tenacious_bench.py
```

## Score

```bash
python3 -m eval.tenacious_bench.scoring_evaluator tenacious_bench_v0_1/dev/tasks.jsonl
```

## Contamination Check

```bash
python3 -m eval.tenacious_bench.contamination_check
```

