# Day 1 — question.md

## Updated Question

My `OpenRouterClient` measures latency as a single wall-clock number — request sent to last byte received — and my memo reports "106 ms latency per task" as a production decision metric. I cannot explain what that number is made of. My call shape is: model `gpt-4.1-mini` via OpenRouter, input prompt of roughly 400–600 tokens (enrichment brief + outreach policy), `max_completion_tokens=350` as a ceiling — but I have never inspected the `usage.completion_tokens` field in the response to know how many tokens are actually generated per call.

What is the prefill/decode cost split for this specific call shape, and which phase is most likely dominating my 106 ms? And given that my actual output token count is unknown, what does `usage.completion_tokens` in the OpenRouter response tell me — and would instrumenting it change which engineering lever I should pull to make the memo's latency claim defensible?

Knowing this forces a concrete engineering choice between three outcomes I cannot currently distinguish:
- If **prefill dominates** — the right fix is shortening the enrichment briefs in `agent/enrichment/`
- If **decode dominates** and output tokens are near the 350 cap — the right fix is reducing `max_completion_tokens`
- If **actual output tokens are already short** (50–80 tokens) — neither lever matters, the 106 ms is mostly network round-trip, and the memo claim is fine as-is but needs to say so explicitly

Right now I cannot choose between these three without understanding the mechanism.

## Connection to Artifact

- **`memo.md` Page 1** — states "Latency per task without the trained component: 106 ms" and "with the trained component: 123 ms" as production decision metrics used to justify the deployment recommendation. The 17 ms delta between baseline and trained component is presented as meaningful, but neither number is decomposed into prefill, decode, network, or queue components anywhere in the repo.
- **`agent/llm/openrouter.py` line 87** — the only place latency is measured in the entire codebase. It is a single `perf_counter()` wall-clock wrap with no phase breakdown:
  ```python
  started = perf_counter()
  with request.urlopen(req, timeout=self.timeout_seconds) as response:
      raw_body = response.read().decode("utf-8")
  latency_ms = int((perf_counter() - started) * 1000)
  ```
- **`agent/llm/openrouter.py` — `OpenRouterChatResult` dataclass** — captures `usage` from the API response but it is never logged or analyzed anywhere in the pipeline:
  ```python
  @dataclass
  class OpenRouterChatResult:
      content: str
      model: str | None
      response_id: str | None
      latency_ms: int
      cost_usd: float = 0.0
      usage: dict[str, Any] | None = None  # captured but never inspected
      raw_response: dict[str, Any] | None = None
  ```
- **`model_card.md` — "Deployment Recommendation" section** — cites inference speed as a factor in the deployment decision without being able to say what drives it, what phase dominates, or which engineering change would actually move the number.

