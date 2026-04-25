# Target Failure Mode: Tone-Marker Drift & Jargon Contamination

The single highest-ROI failure mode identified for the Tenacious agent is **Professionalism & Tone Drift**, specifically the use of "offshore vendor" jargon and filler phrases (e.g., "bench," "top talent," "just checking in").

## 1. Description and Business Cost

Tenacious differentiates itself by being a high-end "Intelligence Corporation" rather than a commodity body shop. When the agent uses vendor clichés, it triggers immediate skepticism from the target audience (CTOs, VPs of Eng).

### Business Cost Derivation

*   **Metric 1: ACV Preservation.**
    *   Target ACV Minimum: **\$[ACV_MIN]** (per `seed/baseline_numbers.md`).
    *   Impact: A single branding violation in a high-value thread can burn a relationship with a 12-month value of \$[ACV_MIN]. If 5% of threads are disqualified due to "vendor-vibe" distrust, it represents an annualized revenue risk of **\$[CALCULATED_RISK_PER_100_LEADS]** per batch of 100 leads.
*   **Metric 2: Stalled-Thread Rates.**
    *   B2B Industry Baseline (Stalled): **72%**.
    *   Mechanism: Trust-erosion is the primary driver of stalled deals in early-stage discovery. Improving tone adherence by 10% is projected to reduce the stalled-deal rate to **65%**, accelerating pipeline velocity.
*   **Metric 3: Brand Reputation Impact.**
    *   Tenacious internal policy: "Tenacious-brand risk from a single viral roast... outweighs a week of reply-rate gains."
    *   Calculated Penalty: One "viral roast" could jeopardize the **520% YoY growth rate** by closing the doors to Tier-1 VC circles where Tenacious finds its Segment 1 (Series A/B) leads.

## 2. Root Cause Analysis
*   **Base Model Bias:** Standard LLMs (OpenRouter/GPT-4o/Claude) are RLHF-trained to be helpful, polite, and use standard business English. This defaults to "Hope you're well" and "A-players," which are explicit violations of the Tenacious Style Guide.
*   **Instruction Overload:** The agent prioritizes "grounding" (Accuracy) over "tone" (Style) when the prompt context is dense.

## 3. Recommended Remediation
*   **Implementation of the Tone-Preservation Check (Act III):** A dedicated evaluation step scoring every draft against the 5 Tenacious markers.
*   **Hard-Constraint Filtering:** RegEx-based blockers on terms like "bench," "offshore," "rockstar," and "ninja."
*   **Negative Prompting:** Explicitly listing forbidden filler phrases in the `GroundingPolicy` system prompt.
