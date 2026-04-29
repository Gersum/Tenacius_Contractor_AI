# Synthesis Memo: Survey on LLM-as-a-Judge

## Design Choice I Disagree With

I disagree with the recurring design choice in the survey's sections on rubric underspecification and judge reliability to treat increasingly capable judge models as the main remedy for rubric ambiguity. The survey is right that LLM judges can be useful, but in this repo that ordering would hide benchmark design weakness instead of solving it. If the judge has to infer what a “good” Tenacious outreach action even is, then the benchmark is still underspecified.

## Why Repo Evidence Pushes Me There

Our own Week 11 artifacts make the constraint concrete. The strongest current benchmark examples are not the ones that rely on model judgment; they are the ones where the evaluator can show its work:

- required-claim coverage
- forbidden-language checks
- expected-action presence
- dimension-specific guardrails such as capacity restraint or uncertainty language

That design came directly from Week 10 evidence. The failure surface was not “the model cannot write English.” It was “the model can write something fluent that still over-claims, sounds like a commodity vendor, or mishandles a scheduling handoff.” Those are exactly the places where a vague judge would be dangerous, because it might reward persuasive rhetoric rather than rubric compliance.

The current codebase reflects that lesson:

- the evaluator is deterministic first
- judge dimensions remain explicit and bounded rather than magical
- the worked examples state when no live judge step is active
- methodology reserves eval-tier judgment for calibration samples, not for the entire benchmark

## Alternative Choice I Defend

For Tenacious-Bench, I would reverse the order implied by the looser judge-first reading of the survey:

1. make the benchmark explicit enough that deterministic checks can score the obvious parts
2. use LLM judgment only on the residual dimensions that genuinely require interpretation
3. document the judge boundary so the benchmark never pretends a model “just knows” the rubric

This is not anti-judge. It is pro-accountability. The repo's own evidence shows that the highest-risk failures are domain-specific and easy to flatter with generic sales fluency. A too-powerful judge introduced too early would make that problem harder to detect.

## Bottom Line

The survey is valuable, but I disagree with the design instinct to let judge capacity compensate for rubric looseness. Our Week 10 and Week 11 evidence both point the other way: define the benchmark sharply first, then add a judge only where the residual ambiguity is real and documented.
