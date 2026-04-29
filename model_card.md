# Model Card: Tenacious Path B Critic

## Status

Scaffolded. The repository includes preference data and training script entrypoint, but the ORPO/SimPO run has not yet been executed in this local environment.

## Intended Use

The critic is intended to reject or route Week 10 conversion-engine outputs that violate Tenacious-specific sales constraints: unsupported claims, off-brand tone, bench over-commitment, competitor-gap over-claiming, scheduling mistakes, and ICP misclassification.

## Base Model

Default scaffold backbone: `Qwen/Qwen2.5-0.5B-Instruct`. The Week 11 brief recommends Qwen 3.5-class small backbones where available; update the script argument before live training.

## Training Data

`training_data/path_b_preference_pairs.jsonl`, derived from the Tenacious-Bench train partition.

## Limitations

- Not yet trained in this repo.
- Current ablation numbers are deterministic scaffold outputs, not a live trained-model result.
- The critic is domain-specific and should not be used as a generic sales-quality model.

