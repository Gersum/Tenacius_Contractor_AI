# Tenacious Failure Taxonomy

This taxonomy groups every probe in [probe_library.md](/Users/gersumasfaw/Downloads/week_10/probes/probe_library.md) into one and only one failure category. The purpose is operational: a successor should be able to look at a failed probe, locate the category-level pattern, and decide whether the right fix belongs in enrichment, orchestration, channel policy, or evaluation.

## Taxonomy Rules

- No orphan probes: every probe ID from the library appears below.
- No double counting: each probe is assigned to a single primary category.
- Aggregate trigger rates: reported at the category level from current development traces and used as the baseline for per-probe risk framing.

## Category Map

| Category | Shared failure pattern | Aggregate trigger rate | Probe IDs |
|---|---|---:|---|
| ICP misclassification | Agent assigns a specific segment or ICP label from incomplete or contradictory public signals. | 12% | ICP-001, ICP-002, ICP-003, ICP-004 |
| Hiring-signal over-claiming | Agent turns weak, stale, or singular public evidence into stronger growth claims than the evidence supports. | 18% | HS-001, HS-002, HS-003, HS-004 |
| Bench over-commitment | Agent promises stack coverage, seniority, or deployment speed beyond the current bench file. | 7% | BOC-001, BOC-002, BOC-003 |
| Tone drift from style guide | Agent defaults to generic B2B filler, vendor jargon, or off-brand formatting. | 22% professionalism, 35% directness, 9% formatting | TONE-001, TONE-002, TONE-003, TONE-004 |
| Multi-thread leakage | Agent exposes another lead's context or internal system state in the current draft. | <1% | LEAK-001, LEAK-002 |
| Cost pathology | Agent uses too many tool calls, too much context, or too expensive a model path for the value of the step. | 5% reasoning loops, 10% high-cost mapping | COST-001, COST-002 |
| Dual-control coordination | Agent mishandles multi-channel sequencing or booking state across email, SMS, and calendar actions. | 7% | DUAL-001, DUAL-002 |
| Scheduling edge cases | Agent mishandles time-zone math, overlap windows, DST transitions, or narrow working-hour intersections. | 15% | TZ-001, TZ-002, TZ-003 |
| Signal reliability | Agent treats weak or ambiguous public evidence as confirmed fact. | 18% | REL-001, REL-002 |
| Competitor-gap over-claiming | Agent overstates peer adoption, uses stale or private evidence, or frames the gap condescendingly. | 18% grounding, 22% tone if phrased poorly | GAP-001, GAP-002, GAP-003, GAP-004 |

## Why These Categories Matter

### 1. ICP Misclassification

This class captures errors that happen before personalization even begins. If a lead enters the wrong segment, every downstream choice can look locally coherent while still being strategically wrong.

### 2. Hiring-Signal Over-Claiming

This is the main "research inflation" category. The agent sees one public signal and writes copy as if it has a full thesis. For Tenacious, this matters because the outbound is supposed to sound like a research finding, not a scraped template.

### 3. Bench Over-Commitment

These failures are specific to talent outsourcing. The message can win the reply and still damage the business if it promises a team shape or start date the delivery organization cannot honor.

### 4. Tone Drift From Style Guide

Tenacious is not competing as a low-cost body shop. Tone drift is therefore not cosmetic; it changes how the company is positioned in the first message.

### 5. Multi-Thread Leakage

Leakage incidents are rare but severe. Even one cross-lead mistake can outweigh a large number of otherwise good replies because it creates a confidentiality event.

### 6. Cost Pathology

This category tracks mechanism inefficiency rather than message quality. The business risk is that a workflow can look high quality but become uneconomic when scaled.

### 7. Dual-Control Coordination

This class covers mistakes where the agent is locally correct inside one channel but globally wrong across channels. Centralized handoff logic is the main mitigation.

### 8. Scheduling Edge Cases

Scheduling failures happen later in the funnel, after a reply has already been earned. That makes them especially costly relative to their raw trigger rate.

### 9. Signal Reliability

These probes focus on false positives. The core issue is not weak personalization; it is claiming something untrue about the prospect's current operating reality.

### 10. Competitor-Gap Over-Claiming

This is the failure mode that turns a differentiated "research-led" message into a bluff. In Tenacious's context, that often shows up as invented peer practices or condescending phrasing toward technically sophisticated buyers.

## Coverage Check

The 30 probe IDs from the library are fully covered:

- ICP: 4 probes
- Hiring signals: 4 probes
- Bench: 3 probes
- Tone: 4 probes
- Leakage: 2 probes
- Cost: 2 probes
- Dual-control: 2 probes
- Scheduling: 3 probes
- Reliability: 2 probes
- Gap claims: 4 probes

Total: 30 probes, 0 orphans, 0 duplicate assignments.
