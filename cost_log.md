# Week 11 Cost Log

## Budget Plan

Challenge envelope: `$10.00`

| Bucket | Reserved budget | Status | Notes |
|---|---:|---|---|
| Dataset authoring | $3.50 | not yet spent | cheap dev-tier OpenRouter synthesis and judge filtering only |
| Training | $3.00 | not yet spent | default target is free Colab T4; RunPod only if Colab fails |
| Held-out evaluation | $2.50 | not yet spent | reserved for 3 to 4 sealed eval-tier passes only |
| Reserve / reruns | $1.00 | not yet spent | bug fixes and one late rerun maximum |

## Actual Charges

| Timestamp | Bucket | Provider | Purpose | Run ID | Cost | Status |
|---|---|---|---|---|---:|---|
| 2026-04-28T00:00:00Z | dataset authoring | local deterministic scripts | Generate Tenacious-Bench v0.1 scaffold | local-scaffold-build | $0.00 | completed |
| 2026-04-28T00:00:00Z | scoring | local deterministic scripts | Score example tasks and scaffolded ablations | local-evaluator-pass | $0.00 | completed |
| 2026-04-28T00:00:00Z | contamination | local deterministic scripts | Run contamination report | local-contamination-pass | $0.00 | completed |
| 2026-04-30T00:00:00Z | training | Google Colab T4 | ORPO LoRA run on Path B preference pairs | colab-orpo-run-1 | $0.00 | completed |
| 2026-04-30T00:00:00Z | held-out smoke test | Google Colab T4 | Single-task held-out generation check on `tb-0169` | colab-heldout-smoke-1 | $0.00 | completed |

## Pending Live Entries

These rows are intentionally unfilled until the runs actually happen.

| Planned run | Expected bucket | Provider | Trigger for adding a real entry |
|---|---|---|---|
| OpenRouter dev-tier synthesis pass | dataset authoring | OpenRouter cheap tier | first paid multi-LLM authoring or dedup call |
| Additional Unsloth Colab training run | training | Google Colab T4 | only if a second iteration is needed after reviewing the first run |
| RunPod fallback training run | training | RunPod 4090 or A40 | only if Colab session caps block completion |
| Held-out sealed evaluation | held-out evaluation | eval-tier OpenRouter route | first eval-tier pass on sealed slice |

## Logging Rule

Every non-zero API or compute charge must be appended with:

- timestamp
- bucket
- provider
- purpose
- run ID
- exact cost
- status

No eval-tier entries should appear here before the held-out phase. No tau2 retail reruns should appear here at all.
