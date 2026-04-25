# Tenacious Failure Taxonomy

Probes are grouped by failure category with observed trigger rates from current development traces.

## 1. Grounding and Integrity
*Failures in citing evidence or mapping data to claims.*

| Category | Description | Observed Rate | Trigger |
|---|---|---|---|
| **Over-claiming** | Asserting stronger signals than provided (e.g., "rapid hiring" for 1 job post). | 18% | Weak HiringSignalBrief + High-temperature LLM. |
| **Misclassification** | Assigning leads to incorrect ICP segments (e.g., Series A as Mid-Market). | 12% | Conflicting CRB data vs. Employee count. |
| **Fabrication** | Hallucinating bench stats or competitor names not in `seed/`. | 4% | Context window overflow or prompt injection. |

## 2. Brand and Tone Policy
*Failures to preserve the Tenacious professional identity.*

| Category | Description | Observed Rate | Trigger |
|---|---|---|---|
| **Professionalism (Jargon)** | Using "bench," "offshore," or "outsource" instead of approved terms. | 22% | Standard LLM training data overriding Style Guide. |
| **Directness (Filler)** | Starting messages with "Hope you're well" or "Just following up." | 35% | Polite-bias in standard system prompts. |
| **Formatting** | Including emojis or marketing taglines in cold outreach. | 9% | Style guide version mismatch. |

## 3. Operational and Coordination
*Failures in scheduling, resource allocation, and cost control.*

| Category | Description | Observed Rate | Trigger |
|---|---|---|---|
| **Timezone Slip** | Suggesting meeting times outside the 3-5 hour overlap window. | 15% | Missing offset calculation in orchestration. |
| **Over-commitment** | Pitching skills with 0 availability in `bench_summary.json`. | 7% | Stale bench cache or greedy brief-matching. |
| **Context Leakage** | Mixing data from multiple leads in the same run. | <1% | Shared state in concurrent pipeline execution. |

## 4. Cost and Efficiency
*Failures to stay within defined budget envelopes.*

| Category | Description | Observed Rate | Trigger |
|---|---|---|---|
| **Reasoning Loops** | Excessive tool-call iterations for a single draft. | 5% | Ambiguous grounding rules leading to retries. |
| **High-Cost Mapping** | Using expensive models for low-value enrichment steps. | 10% | Configuration error in `agent/config.py`. |
