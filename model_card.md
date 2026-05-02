# Model Card: Tenacious Path B Critic

## Status

A first live Path B run has been completed on **Google Colab T4** using `ORPO` with a LoRA adapter on `Qwen/Qwen2.5-0.5B-Instruct`.

That means the training stack is no longer scaffold-only. However, the first held-out smoke test did **not** show lift over baseline, so this adapter should still be treated as experimental.

## Intended Use

The adapter is intended for research and evaluation on Tenacious-specific sales-agent outputs. The target use case is a critic or correction layer that rejects or routes outputs that violate:

- public-signal restraint
- Tenacious tone constraints
- bench-capacity honesty
- competitor-gap humility
- scheduling handoff correctness
- ICP uncertainty handling

## Base Model

- backbone: `Qwen/Qwen2.5-0.5B-Instruct`
- training method: `ORPO`
- adaptation method: `LoRA`
- training platform: `Google Colab T4`

## Training Data

Source file: `training_data/path_b_preference_pairs.jsonl`

Run summary:

- train rows: `94`
- eval rows: `11`
- global steps: `24`
- epoch count: `1.0`
- runtime: `97.7594` seconds
- final train loss: `1.5820321440696716`

## Evaluation Summary

Current evidence is mixed:

- mechanical training execution: successful
- held-out generation quality: weak

On held-out smoke test task `tb-0169` (`tone_style_drift`):

- baseline score: `0.2`
- trained-adapter score: `0.2`

So the adapter did not show useful lift on that first held-out rewrite check.

## Limitations

- this is a first-pass ORPO run, not an optimized final model
- the current evaluation result does not support replacing the Week 10 generator
- held-out evaluation has not yet been completed across the full sealed slice
- the adapter is domain-specific and should not be used as a general sales or writing model

## Deployment Recommendation

Do **not** deploy this adapter as a production rewrite replacement yet. The right next step is broader held-out evaluation and, if needed, a second iteration with improved training formatting or a stricter critic-style inference setup rather than free-form rewriting.
