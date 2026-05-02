# Unsloth Colab Runbook

This file exists because the challenge expects a **real** training-stack execution, not just a training script placeholder.

## Goal

Confirm a live Unsloth-compatible Path B run on Google Colab T4 before the held-out evaluation phase.

## Pre-Flight Checklist

- HuggingFace account created
- HuggingFace write token available
- Google Colab T4 runtime tested
- OpenRouter key set for any dev-tier authoring that still needs to happen
- `training_data/path_b_preference_pairs.jsonl` present
- `cost_log.md` updated before and after the run

## Planned Configuration

- training path: `Path B`
- training method: `ORPO or SimPO`
- backbone family: `Qwen 3.5 small backbone`
- adapter method: `LoRA`
- framework: `Unsloth`
- target runtime: `Colab T4`

## Minimum Run Evidence Required

To count as a real run, commit or capture all of the following:

1. start timestamp
2. exact backbone name
3. hyperparameters
4. dataset row count used
5. train loss snapshots
6. validation metric snapshots if available
7. wall-clock duration
8. whether the run converged before the 30-minute kill threshold
9. whether an adapter was pushed to HuggingFace

## Kill Criterion

If training does not show stable loss movement within `30 minutes`, stop the run and inspect:

- preference-pair quality
- prompt formatting
- backbone / precision mismatch
- corrupted labels or duplicate rows

Do **not** keep spending compute just because the run started successfully.

## Post-Run Actions

- replace `training/training_run.log` with the real run log
- append exact cost or `$0.00` to `cost_log.md`
- update `methodology.md` if the chosen training configuration changes
- add HuggingFace dataset / model URLs once publication exists
