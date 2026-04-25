# Memo: Tenacious Intelligence Agent Strategy

## Page 1: The Decision

### Executive Summary
We built the **Tone-Anchored Multi-Stage Grounding (TAMSG)** conversion engine to turn public-company signals into Tenacious-aligned outreach, qualification, and scheduling actions. On the sealed held-out evaluation, TAMSG achieved **89.1% Pass@1**, up from the Day-1 baseline of **72.67%**, a gain of **16.43 percentage points** at roughly flat unit cost (**$0.0212** vs. **$0.0199** per task). We recommend a **30-day pilot in Segment 01 (Recently Funded Series A/B) at 60 thoughtful touches per week with a $50 weekly software cap; proceed only if grounded outreach delivers at least a 7% reply rate and keeps stalled threads below 15% within the 30-day window**.

### Cost per Qualified Lead
For this memo, a **qualified lead** is defined as a thread that reaches the `qualify_reply` step in `artifacts/traces/agent_trace_log.jsonl`. In the current runtime trace sample, **27 of 31** synthetic prospect interactions reached `qualify_reply`, so the qualified-lead rate is **87.1%**. Using the sealed-eval TAMSG average LLM cost of **$0.0212 per task**, the visible derivation is:

`cost per qualified lead = $0.0212 x (31 total threads / 27 qualified threads) = $0.0243`

Input decomposition:
- **LLM spend per task:** **$0.0212** (`ablation_results.json`, `tamsg_method`)
- **Trace denominator:** **31** total runtime threads (`artifacts/traces/agent_trace_log.jsonl`)
- **Qualified threads:** **27** reached `qualify_reply` (`artifacts/traces/agent_trace_log.jsonl`)
- **Derived cost per qualified lead:** **$0.0243**

This is not a full live-production CAC number because it excludes human review time and external API overhead, but it is a transparent synthetic unit-cost estimate and is far below the cost of a human-written touch.

### Speed-to-Lead Delta: Stalled-Thread Rates
For this memo, a **stalled thread** uses the challenge definition from `seed/email_sequences/reengagement.md`:

`stalled_rate = (prospects who replied engaged/curious but did not book within 14 days) / (total prospects who replied engaged/curious)`

Measured against the current synthetic trace set:
- **Manual Tenacious baseline:** **30-40%** stalled threads (`seed/email_sequences/reengagement.md`)
- **TAMSG measured sample:** **0 of 27 qualified-reply threads stalled**, or **0.0%** (`artifacts/traces/agent_trace_log.jsonl`)
- **Delta vs. baseline:** **30-40 percentage points lower**

This is directionally strong but should be treated as **suggestive rather than conclusive**, because the denominator is a synthetic sample and some booking outcomes used fallback or local-integration scaffolding rather than a fully externalized production stack.

### Competitive-Gap Outbound Performance
Two outbound variants matter commercially:
- **Signal-grounded outbound:** outreach anchored on public signals, specifically **AI maturity scoring plus a top-quartile competitor gap**
- **Generic outbound:** a general Tenacious capability pitch without prospect-specific signal grounding

The repo does **not** contain a clean randomized A/B log with both variants and measured reply counts, so I am treating the reply-rate comparison as **benchmark-informed, not an in-repo causal estimate**. The relevant public benchmark ranges from `seed/baseline_numbers.md` are:
- **Signal-grounded outbound reply rate:** **7-12%**
- **Generic cold outbound reply rate:** **1-3%**
- **Delta:** **6-9 percentage points**; midpoint delta **7.5 percentage points**

Sample context from our own system: the current runtime trace contains **31 synthetic interactions** and **27 qualified-reply threads**, and the outreach path in those traces uses the grounded prompt path rather than a generic randomized control. That means the benchmark delta is appropriate for **pilot planning**, but not yet for a hard causal claim.

### Pilot Scope Recommendation
- **Segment:** **01 — Recently Funded Series A/B**
- **Lead volume:** **60 thoughtful touches per week** (matches Tenacious internal SDR operating target)
- **Budget:** **$50 per week software budget** for LLM and workflow overhead during the 30-day pilot
- **30-day success criterion:** **Proceed only if grounded outreach reaches at least a 7% reply rate and keeps stalled threads below 15% over the pilot window**

Why this segment: it is the most natural fit for a signal-grounded motion because funding events are public, fresh, and easy to verify, which lowers hallucination risk and gives the model a concrete reason to open the conversation.

---

## Page 2: The Skeptic's Appendix

### Failure Modes Beyond τ²-Bench
1. **"Offshore-vibe" objection.** A prospect reads Tenacious as a commodity staffing shop instead of a high-context engineering partner. The mechanism still "completes the task," but the business outcome is negative because brand trust erodes before discovery.
2. **Bench mismatch drift.** The outreach mentions a skill cluster that is no longer current in the delivery bench. The model may be factually consistent with stale grounding but commercially wrong, leading to low-quality meetings and wasted AE time.
3. **Brand-reputation roast.** A competitor-gap message is directionally correct but phrased too sharply. The likely failure is not a bad benchmark score; it is brand damage from sounding smug or adversarial.
4. **Cross-thread context leakage.** In a multi-company rollout, the system could accidentally reuse an insight pattern too specifically across accounts. That creates confidentiality risk even if each single-thread response appears fluent.

### Public-Signal Lossiness: AI Maturity Scoring
- **False negative mode — Quietly sophisticated.** A company may show few or no public AI job posts while still operating a capable internal AI or data-science function.
  - **Wrong agent action:** It under-segments the account, skips the specialized-capability-gap hook, or sends a low-conviction generic note.
  - **Business impact:** Tenacious wastes a scarce high-quality touch and misses the chance to position against a real delivery gap.

- **False positive mode — Loud but shallow.** A company may post multiple "AI" roles that are actually generic application-development or platform-maintenance jobs.
  - **Wrong agent action:** It overstates the prospect's AI maturity and pitches Segment 04-style transformation credibility that the buyer has not actually earned.
  - **Business impact:** Tenacious looks presumptuous, damages credibility early, and risks a segment mismatch that depresses reply quality even if the prospect answers.

### Honest Unresolved Failure From the Mechanism
**Failure BOC-003 — Nairobi time-zone gap during SMS handoff.** In the probe library, the model can still suggest impossible East Africa Time windows for West Coast prospects when fallback scheduling moves to SMS and the model is reasoning under pressure instead of relying on a deterministic calendar check.

- **Probe category:** scheduling / time-zone reasoning failure under multi-turn pressure
- **Triggering condition:** late-stage handoff after qualification, especially when the thread moves from email into fallback SMS scheduling
- **What the mechanism still gets wrong:** it produces a slot that sounds polite and specific but is operationally impossible for the buyer
- **Business impact if deployed anyway:** each failure burns a high-intent thread at the last mile, creating avoidable rework for the AE and converting a qualified conversation into a stalled one; at a planning level, even a 15% failure rate in SMS handoffs would mean **150 broken scheduling attempts per 1,000 handoff threads**

The memo recommendation therefore assumes a **guardrail**: do not scale SMS fallback scheduling beyond the pilot until slot selection is deterministic and time-zone normalized before the message is drafted.
