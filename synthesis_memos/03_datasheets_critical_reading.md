# Synthesis Memo: Datasheets for Datasets

## Design Choice I Disagree With

I disagree with the paper's tendency to treat the datasheet primarily as a disclosure artifact that sits adjacent to the dataset rather than as an active design constraint on what gets built in the first place. That is a reasonable framing for mature datasets that already exist, but it is too passive for Tenacious-Bench.

## Why Repo Evidence Pushes Back

Our own Week 11 work shows that the hardest problems appeared before publication, not after it. The biggest benchmark risks were:

- mixing source modes with very different trust profiles
- quietly leaking held-out assumptions into train-facing documentation
- over-claiming evaluator reliability before the human relabel cycle is done

Those are not “final documentation” problems. They are dataset-construction problems. The repo only became more coherent once the datasheet requirements started affecting design decisions directly:

- `train`, `dev`, and `held_out` were made explicit in the package structure
- source mode became first-class metadata instead of hidden provenance
- contamination-check outputs were committed as named artifacts
- README and methodology had to state clearly that inter-rater agreement is still pending

Without that pressure, it would have been easy to publish something benchmark-shaped but not benchmark-disciplined.

## Alternative Choice I Defend

For Tenacious-Bench, the datasheet should function as an architectural forcing mechanism:

1. define what must be true before a task is admitted
2. force provenance, split, and licensing decisions to be explicit
3. block publication claims that the evidence graph cannot support

That is closer to how the repo actually improved. The datasheet was useful when it changed implementation and packaging behavior, not only when it described the final result.

## Bottom Line

The paper is directionally right, but I disagree with the softer “document afterward” instinct. In this repo, the strongest effect of datasheet thinking was upstream: it forced clearer split discipline, clearer provenance, and more honest limits around inter-rater and held-out claims.
