# signoff.md

**Asker:** Gersum Asfaw
**Explainer written by:** Amir Ahmedin
**Topic:** Inference-time mechanics — prefill/decode latency decomposition
**Date:** Day 1, Week 12
**Published artifact:** https://medium.com/p/129e4a8a623e?postPublishedType=initial
**Published thread:** https://x.com/i/status/2051742853177528453

---

## Gap Status: CLOSED ✅

---

## What I Now Understand

Before this explainer, I measured latency as a single wall-clock number and reported "106 ms latency per task" in memo.md as if it were a meaningful production metric. I could not explain what was inside that number or which engineering lever would move it.

After reading Amir's explainer, I now understand:

**1. The four components of my wall-clock measurement**
My 106 ms contains network round-trip (~15–40 ms), queue wait (0–50 ms), prefill (~3–8 ms for my 400–600 token prompts on gpt-4.1-mini), and decode (~0.35 ms per output token). These components respond to different levers — network is fixed, prefill scales with input length, decode scales with actual output tokens generated.

**2. Which phase most likely dominates my number**
For gpt-4.1-mini with 400–600 input tokens, prefill is fast (~5 ms). Whether network or decode dominates depends entirely on how many tokens the model actually generates — which I have never inspected. The `usage.completion_tokens` field is captured in my `OpenRouterChatResult` dataclass but never logged or analyzed anywhere in the pipeline. That is the instrumentation gap I need to close.

**3. Why `max_completion_tokens=350` may be irrelevant**
It is a ceiling, not a request. If the model naturally stops at 70 tokens, changing the ceiling from 350 to 150 has zero effect on latency. Reducing it only helps if the model is consistently hitting the cap — which I cannot know without logging `completion_tokens`.

**4. What the 17 ms delta between baseline and trained component actually means**
The explainer's observation that the 17 ms delta is likely real and attributable to either longer input context (trained component adds adapter instructions → more prefill) or longer outputs (trained component generates more verbose responses → more decode) gives me a concrete hypothesis to test by instrumenting both paths.

**5. How to get exact decomposition**
Using `stream=True` gives time-to-first-token (network + queue + prefill) and time-from-first-to-last-token (pure decode). This is the direct measurement path that removes estimation entirely.

---

## What Changes in My Portfolio

The gap closure produces a concrete edit to memo.md. The latency line on Page 1 will be rewritten from:

> "Latency per task without the trained component: 106 ms"

To:

> "Latency per task without the trained component: 106 ms (wall-clock, request-send to last-byte-received). This number contains network round-trip, queue wait, prefill, and decode. For gpt-4.1-mini with 400–600 input tokens, prefill is estimated at ~5 ms. Whether the remaining ~100 ms is network-dominated or decode-dominated depends on actual output token count, which has not been instrumented. Recommend logging `usage.completion_tokens` across 10 tasks to determine which engineering lever applies."

This is a commit I can defend if a senior engineer pushes back. The old line could not be defended at all.

---

## One Note on the Explainer

The hands-on instrumentation code is correct and points directly at the right field (`usage.completion_tokens` in `OpenRouterChatResult`). The only gap is that actual output numbers from a real run were not included — the section describes what the output would look like rather than showing it. This did not prevent gap closure, as the mechanism and the measurement path are both fully clear. Flagged as a pattern to address in future explainers.
