# Synthesis Memo: ORPO / SimPO for Path B

## Design Choice I Disagree With

I disagree with the implicit expectation in preference-optimization work that a successful optimization run should be read quickly as a likely generation-quality win. For Path B in this repo, that is the wrong interpretation target.

## Why Repo Evidence Pushes Back

Our own first real ORPO run is the key evidence:

- platform: Google Colab T4
- backbone: `Qwen/Qwen2.5-0.5B-Instruct`
- train rows: `94`
- eval rows: `11`
- runtime: `97.7594s`
- final train loss: `1.5820`

Technically, that is a real success. But the held-out smoke check recorded in `training/training_run.log` stayed flat:

- task `tb-0169`
- baseline score `0.2`
- trained score `0.2`

That result matters because it shows the gap between “the optimization procedure ran” and “the resulting artifact improved the thing we care about.” In Tenacious-Bench, the thing we care about is not generic response preference. It is compliance with narrow Tenacious rules under held-out conditions.

## Alternative Choice I Defend

For Path B here, the right evaluation posture is:

1. treat successful ORPO/SimPO execution as infrastructure validation
2. treat held-out lift as a separate question
3. refuse deployment claims unless held-out evidence improves

That is stricter than how these methods are sometimes discussed, but it matches the repo evidence. The benchmark is doing its job if it lets us say the run was technically successful but operationally weak.

## Bottom Line

I do not disagree with ORPO or SimPO as methods. I disagree with the too-easy reading that a clean training curve implies practical success. In this repo, the honest finding is that the first ORPO run succeeded mechanically and still failed to show useful held-out rewrite lift.
