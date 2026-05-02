Tenacious-Bench Final Memo

[[PAGE 1]]

Page 1 - The Decision

Executive summary
Tenacious-Bench v0.1 shows a deterministic held-out Delta A lift of +0.2381 average score points over the Week 10-style baseline, with a reported 95% confidence interval of [0.08, 0.18] and paired bootstrap p = 0.031 on 42 held-out tasks. Delta B is flat in the current scaffold: on the same backbone and the same correction-task shape, the prompt-only control averages 0.619 while the critic-correction path averages 0.8571, but the first live ORPO smoke test on task tb-0169 was 0.2 to 0.2, so the trained adapter has not yet reproduced the scaffolded lift. Recommendation: do not deploy the trained Path B component yet; keep the benchmark and deterministic correction harness, and only promote the learned critic after a broader held-out pass shows positive lift, stable behavior outside rewrite-friendly cases, and acceptable production monitoring metrics.

Decision details
- Headline Delta A: baseline average score 0.6190, critic-correction average score 0.8571, lift +0.2381 on the 42-task held-out slice.
- Statistical read: paired bootstrap p = 0.031; reported 95% CI [0.08, 0.18] from the committed ablation scaffold.
- Delta B, reported honestly: on the same backbone and the same intervention shape, prompt-only average score is also 0.6190, so the current advantage comes from the deterministic critic-correction path, not from a proven learned-model gain.
- Cost per task without the trained component: $0.0212; with the trained component: $0.0241.
- Latency per task without the trained component: 106 ms; with the trained component: 123 ms.

Production recommendation
Do not deploy the trained Path B adapter as a production guardrail yet. The recommendation rests on three facts carried forward from the evidence above: the scaffolded held-out lift is +0.2381, the learned smoke test is flat at 0.2 to 0.2 on tb-0169, and the added component still raises cost from $0.0212 to $0.0241 per task. What should stay: the benchmark, evidence graph, contamination checks, and standard-field HubSpot integration are all deployment-useful today. What must change before deployment: complete the 30-task inter-rater cycle, run a full held-out evaluation for the trained critic rather than the scaffold alone, and show that the learned component beats the prompt-only control without introducing new tone or grounding regressions.

Evidence anchors
- Held-out benchmark results: ablations/ablation_results.json and ablations/held_out_traces.jsonl
- Live Path B run status: training/training_run.log
- Dataset publication: https://huggingface.co/datasets/recordabebe/tenacious_bench_v0_1

[[PAGE 2]]

Page 2 - The Skeptic's Appendix

What Tenacious-Bench v0.1 still does not capture
- Cross-account repetition risk. v0.1 scores single outputs well, but it does not yet detect whether a model reuses the same outreach pattern too aggressively across many prospects. v0.2 should add campaign-level diversity checks and near-duplicate clustering across batches.
- Downstream meeting quality. v0.1 measures whether outreach is grounded and compliant, not whether the resulting meetings are worth AE time. v0.2 should join benchmark tasks to post-meeting quality labels and no-show outcomes.
- Human escalation quality. v0.1 checks whether the agent abstains or softens claims, but not whether the handoff package to a human seller is complete and decision-useful. v0.2 should score escalation summaries, missing-context rates, and SLA compliance.
- Long-horizon thread recovery. v0.1 is mostly single-turn or short-horizon. It does not yet capture how the system behaves after a skeptical reply, a calendar failure, or a week-long pause. v0.2 should add multi-turn recovery trajectories with state carryover.

Public-signal lossiness
Ground truth is lossy because AI maturity, hiring intensity, and competitor gaps are inferred from public traces such as job posts, funding events, and team pages. Quietly sophisticated companies can look immature in public data, while loud but shallow companies can look more advanced than they are. In practice, that means the current benchmark can over-reward cautious generic grounding and under-reward sharper personalization that would be justified by private referral context or fresher internal account knowledge. The operational fix for v0.2 is to attach confidence bands and provenance windows to every public-signal claim and score the model separately on calibration, not just final wording.

Honest unresolved training failure
The first live ORPO run was a technical success on Colab T4, but the held-out smoke test on tb-0169 showed no gain: baseline 0.2, trained output 0.2. The failure mode is straightforward: the learned adapter still drifts into explanation or prompt-echo behavior when asked to rewrite weak outreach, so it is not yet reliable as a replacement for the Week 10 generator or as a production critic. Tightening the prompt shape reduced raw prompt echoing but did not produce a score lift, so the next fix would be to retrain on shorter rewrite-format preference pairs and evaluate the model as a critic layer before asking it to generate full rewrites.

Kill-switch trigger
Disable the trained component immediately if any of the following occurs in production: complaint rate on trained-component sends rises above 2% over any rolling 100-send window, grounded-output violations exceed 5% on the weekly human review sample, or cost per qualified thread rises above the baseline path by more than the observed $0.0029 per-task uplift without a matching reply-rate gain. Those thresholds are justified by the current memo evidence: the measured cost delta is small, the learned lift is not yet proven, and there is no room to accept a quality regression in exchange for extra spend. If the kill switch fires, fall back to the deterministic baseline path and reroute failures for rubric or data-pipeline debugging before another training run.
