# Target Failure Mode: Scheduling Edge Cases Across East Africa, Europe, and the US

The single best near-term target for remediation is **scheduling edge cases**, especially wrong overlap assumptions between East Africa-based Tenacious operators and US or EU prospects. This failure mode wins over tone drift and bench over-commitment on ROI because it triggers late in the funnel, after interest has already been earned, and because the fix is highly mechanistic rather than taste-based.

## 1. Why This Failure Mode Wins

### Candidate A: Scheduling Edge Cases

- Aggregate trigger rate: 15% in current development traces.
- Root cause: missing or inconsistent time-zone normalization, daylight-savings handling, and overlap-window enforcement.
- Why it matters: the failure happens after a prospect has already engaged enough to discuss time, so the agent is risking a warm thread rather than a cold lead.

### Candidate B: Tone Drift

- Aggregate trigger rate: 22% professionalism drift, 35% directness drift, 9% formatting drift.
- Why it did not win: the category is frequent, but the remediation space is softer and more subjective. Some tone issues hurt reply odds, but many do not create an immediate, objectively broken workflow event.

### Candidate C: Bench Over-Commitment

- Aggregate trigger rate: 7%.
- Why it did not win: the business severity is high when it fires, but it happens less often and is already partially constrained by the explicit `bench_summary.json` honesty rule.

## 2. Business Cost Derivation

The business case here is framed in Tenacious's own operating units rather than placeholder ACV values.

### Arithmetic

1. Tenacious SDR target volume is about **60 thoughtful touches per person per week**.
2. Top-quartile signal-grounded outbound reply rate is **7 to 12%**.
3. That implies **4.2 to 7.2 replies per week** from 60 touches.

Formula:

```text
replies_per_week = 60 touches * 0.07 to 0.12
                 = 4.2 to 7.2 replies
```

4. Scheduling edge cases trigger at **15%** in the current taxonomy.
5. If that failure rate carries into warm scheduling threads, the agent puts **0.63 to 1.08 reply-positive threads per week** at risk.

Formula:

```text
threads_at_risk = 4.2 to 7.2 replies * 0.15
                = 0.63 to 1.08 warm threads per week
```

6. Over a four-week pilot, that becomes **2.52 to 4.32 warm threads at risk per SDR-equivalent seat**.

Formula:

```text
monthly_threads_at_risk = 0.63 to 1.08 * 4
                        = 2.52 to 4.32
```

7. Tenacious's re-engagement baseline says **30 to 40%** of replied threads stall in the manual process. Scheduling mistakes are exactly the kind of avoidable coordination error that can push a warm reply back into that stalled bucket instead of toward booking.

### Business Interpretation

Losing even two to four warm threads per month to preventable scheduling math is more painful than losing the same number of cold opens, because the research, qualification, and tone work have already been paid for. This failure mode therefore destroys higher-value workflow moments than a typical cold-email defect.

## 3. Why This Is a Tenacious-Specific Problem

Tenacious operates with a stated **3 to 5 hour/day** standard overlap with client time zones. That overlap is one of the company's core delivery and communication promises. A scheduling agent that ignores real overlap windows is not making a generic SaaS bug; it is violating a public operating promise tied to how Tenacious sells distributed delivery.

This is particularly acute for:

- East Africa to US East Coast coordination, where the overlap is workable but narrow.
- East Africa to US West Coast coordination, where the overlap can shrink to 1 to 2 hours.
- Europe during daylight-savings transitions, where naive local-time handling creates off-by-one-hour booking errors.

## 4. Root Cause

This failure mode is driven by mechanism gaps, not vague model quality:

- The agent reasons in local wall-clock labels too early instead of normalizing to UTC.
- Overlap enforcement happens inconsistently across email, SMS, and booking steps.
- DST transitions are easy to miss when the system carries forward a previously valid offset.
- Warm-thread urgency encourages the model to "be helpful" by suggesting times quickly rather than validating the overlap policy first.

## 5. Why Fixing It Is High ROI

The remediation path is narrow and testable:

1. Normalize all candidate times to UTC before draft generation.
2. Enforce a hard overlap-window policy in orchestration.
3. Reject or rewrite suggestions outside the 3 to 5 hour overlap rule.
4. Persist booking state in UTC and render local labels only at the final channel edge.

Compared with tone drift, this is easier to turn into deterministic guardrails. Compared with bench over-commitment, it fires more often. That combination makes it the best next failure mode to attack.

## 6. Success Condition for the Mechanism

The target outcome is to push the scheduling-edge-case trigger rate materially below the current 15% baseline while preserving booking throughput. A practical engineering target is:

- reduce scheduling-edge-case trigger rate below 5% in the probe set
- keep replies progressing into booking attempts without adding obvious latency or coordination churn

That target is concrete enough for ablation and evaluation, and it maps directly to the warm-thread risk arithmetic above.
