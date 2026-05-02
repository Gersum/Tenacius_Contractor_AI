# Synthesis Memo: Data Contamination in Benchmarking

## Design Choice I Disagree With

I disagree with the common benchmarking habit, reflected in contamination-survey discussions, of treating overlap detection as mostly a model-exposure problem rather than also a benchmark-authoring problem. That framing is too downstream for Tenacious-Bench.

## Why Repo Evidence Pushes Back

In this repo, contamination risk came less from web-scale memorization and more from how easy it is to generate near-duplicate benchmark rows from a small source pool. The benchmark draws from:

- Week 10 traces
- seeded Tenacious materials
- probe expansions
- hand-authored adversarial rewrites

That combination makes local duplication a more immediate threat than internet-scale memorization. The evidence is in the package design itself:

- `contamination_check.json` exists because we needed train/held-out separation discipline inside the repo
- source-mode metadata is retained because contamination risk differs by authoring path
- the publish script now excludes `held_out/` by default because sealed evaluation is a packaging decision, not just an analysis footnote

So while the survey is useful, its emphasis can mislead a small benchmark project into thinking contamination is mainly about model training history. For us, it was equally about local benchmark hygiene.

## Alternative Choice I Defend

For a benchmark of this scale, I would make contamination prevention start at authoring time:

1. preserve source-mode identity
2. keep held-out physically separate in the publication path
3. run overlap checks before writing any headline claim
4. refuse to publish the sealed split by default

That is what the repo now does more explicitly after the Hugging Face publication path was added.

## Bottom Line

I agree with the survey that contamination matters, but I disagree with the tendency to make it feel like a distant pretraining issue. In Tenacious-Bench, contamination was first a repo-construction and publication-discipline issue, and the benchmark got better when we treated it that way.
