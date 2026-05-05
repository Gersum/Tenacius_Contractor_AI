# grounding_commit.md

**Asker:** Gersum Asfaw
**Day:** 1
**Grounded artifact:** `memo.md`
**Date:** Week 12 Day 1

---

## Pointer to the Actual Edit

- `/Users/gersumasfaw/Downloads/week_10/memo.md:15`

I updated the latency bullet in `memo.md` so it no longer presents `106 ms` and `123 ms` as unexplained production-speed facts. The revised line now states that both numbers are **wall-clock request-send to last-byte-received measurements** and explicitly names the components they currently conflate: network round-trip, provider queue time, prefill, and decode. It also reframes the `17 ms` gap as an observed end-to-end difference rather than a defensible model-speed claim until I log `usage.completion_tokens` or use streaming instrumentation to separate first-token from last-token timing.

This change is grounded directly in the gap I closed today. Before the explainer, I was using latency as a decision metric without being able to say what phase dominated it or which engineering lever would move it. After the explainer, I can now defend the memo honestly: the number is still useful, but only as a wall-clock measurement with clear uncertainty about phase attribution. That is a materially better claim than the original bare latency line, and it changes how I would discuss deployment tradeoffs with an FDE or senior engineer reviewing the project.
