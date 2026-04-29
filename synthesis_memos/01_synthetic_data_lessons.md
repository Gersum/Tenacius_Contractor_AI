# Synthesis Memo: Best Practices and Lessons Learned on Synthetic Data for Language Models

## Design Choice I Disagree With

I disagree with the paper's broad bias toward scaling synthetic generation volume once a seed pipeline is in place, especially in its sections on generation diversity and iterative expansion. That choice makes sense for pretraining or broad instruction tuning, but it is the wrong default for Tenacious-Bench. In this repo, the limiting factor is not volume. It is whether a generated task stays diagnostically sharp, contamination-safe, and mechanically scoreable.

## Why My Evidence Pushes Back

Week 10 gave us exactly the kind of small, uneven source pool the paper is trying to rescue: traces, probes, seeded briefs, and style rules, but no benchmark-ready corpus. The tempting move would be to turn that into a large synthetic benchmark quickly. Our own Week 11 evidence argues against that. The strongest artifacts are not the most numerous ones; they are the ones with the clearest provenance and the cleanest rubric path.

Concretely:

- the benchmark now separates `trace_derived`, `programmatic`, `multi_llm_synthesis`, and `hand_authored_adversarial` tasks instead of pretending all synthetic rows carry the same trust profile
- the scoring evaluator only works because each task stores required claims, forbidden claims, expected action, and dimension-specific guardrails explicitly
- the contamination check passes because held-out tasks were generated with reproducibility and separation in mind, not with a “more is better” objective

That is why I disagree with the paper's implicit optimization target. For Tenacious-Bench, aggressive synthetic expansion would have been the wrong move. It would have made the benchmark look larger while making the rubric less believable.

## Alternative Choice I Defend

The repo uses provenance-aware expansion instead:

1. preserve source mode in the schema
2. keep deterministic scoring as the first gate
3. reserve multi-LLM generation for a smaller slice with route metadata
4. treat adversarial authoring as a distinct mode, not noise around the same template

That is a direct response to our own evidence, not just a philosophical preference. Week 10 traces showed the agent can already produce fluent copy. Week 11 needs tasks that expose where fluent copy still fails Tenacious constraints.

## Bottom Line

The paper is useful, but I think it overweights synthetic scale relative to provenance and scoreability for a benchmark like this one. In Tenacious-Bench, the right adaptation is not “generate more.” It is “generate only what can survive contamination checks, preserve source identity, and be graded without hand-waving.”
