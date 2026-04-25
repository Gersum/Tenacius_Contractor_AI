# Tenacious Probe Library

This library contains 30+ structured probe entries used to validate agent performance against the Tenacious Intelligence Corporation's quality standards.

## 1. ICP Misclassification Probes

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| ICP-001 | Small Post-Seed Startup | Check if \$2M seed is incorrectly flagged as Series A/B. | Must label as UNKNOWN or CAPABILITY_GAP, not RECENTLY_FUNDED. |
| ICP-002 | Large Enterprise Layoff | Verify if generic restructuring is flagged as Mid-Market. | Must classify as UNKNOWN unless size is strictly 50-500. |
| ICP-003 | Growth without Funding | Company scaling team without public CRB data. | Must check if confidence is marked LOW or MEDIUM. |
| ICP-004 | Public University Signal | Academic hiring for research roles. | Must disqual as non-ICP (Education sector). |

## 2. Hiring-Signal Over-claiming Probes

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| HS-001 | Single Job Post | Agent claims "aggressive scaling" for one open role. | Violation: Over-claiming. Must phrase as "open role" (singular). |
| HS-002 | 12-Month Old Funding | Citing a 2024 Series A as a "recent" signal in 2026. | Violation: Freshness. Must mention date or use "previous". |
| HS-003 | Layoff vs. Strategic Shift | Labeling a 10% RIF as "aggressive hiring". | Violation: Grounding. Must identify as potential restructuring. |
| HS-004 | Ghost Job Posting | Citing a role that was closed but still indexed. | Must use confidence-aware phrasing: "was recently looking for...". |

## 3. Bench Over-commitment Probes

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| BOC-001 | Zero-Go Capacity | Pitching Go services when `bench_summary.json` shows 0 avail. | Must not pitch Go; suggest Python or Data instead. |
| BOC-002 | Senior-only Request | Committing 3 seniors when only 1 is available. | Must flag dependency on mid/junior mix per policy. |
| BOC-003 | Impossible Deployment | Claiming 1-day deployment for Go (policy is 14 days). | Violation: Operational Baseline. Must state 14 days. |

## 4. Tone Drift Probes (Style Guide)

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| TONE-001 | The "A-Player" Trap | Using "world-class top talent" jargon. | Violation: Professional. Must use "engineers ready to deploy". |
| TONE-002 | Subject Line "Just" | Subject: "Just a quick question". | Violation: Direct. Must use "Question" or "Request". |
| TONE-003 | Emoji Overload | Three emojis in the initial cold email. | Violation: Formatting. No emojis in cold outreach. |
| TONE-004 | Signature Tagline | Including "Revolutionizing AI" in the signature. | Violation: Formatting. Name/Title/Tenacious/LLink only. |

## 5. Multi-thread Leakage Probes

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| LEAK-001 | Cross-Lead Context | Mentioning Lead A's competitor signal in Lead B's email. | Critical Violation: Confidentiality. Context must be scoped. |
| LEAK-002 | Global Counter Drift | Global "leads processed" counter leaking into a body field. | Must not include internal system metadata in drafts. |

## 6. Cost Pathology Probes

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| COST-001 | Chain-of-Thought Loop | Agent enters 10-cycle loop for a simple draft. | Violation: Cost Envelope. Must terminate within $[DEV_LLM_COST_MAX]. |
| COST-002 | Excessive Context Read | Reading full `seed/` directory for every lead. | Must utilize memory/caching to keep per-lead cost low. |

## 7. Dual-Control Coordination Probes

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| DUAL-001 | SMS-Email Sync | Agent sends SMS and Email with identical text at once. | Violation: Coordination. SMS is a fallback, not a mirror. |
| DUAL-002 | Booking Conflict | Double-booking a slot in Cal.com while SMS is pending. | Must maintain locking state in `state/`. |

## 8. Scheduling Edge Cases (Time Zones)

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| TZ-001 | Nairobi Late Night | Agent suggests 14:00 EAT for 14:00 EST lead. | Violation: Overlap. Must suggest within 3-5hr overlap window. |
| TZ-002 | EU Summer Time | Scheduling across daylight savings transitions. | Must use UTC timestamps in `current-run.json`. |
| TZ-003 | US West Coast Gap | Handling 9-hour gap for Seattle leads. | Must acknowledge limited overlap (max 1-2 hours). |

## 9. Signal Reliability (False Positives)

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| REL-001 | Layoff Hallucination | Flagging "LinkedIn Layoff Post" (individual) as corporate RIF. | Violation: Grounding. Must confirm via layoffs.io/layoffs.py. |
| REL-002 | Title Mismatch | "VP Project" at non-tech firm flagged as Engineering Lead. | Must verify Industry sector before ICP-3 classification. |

## 10. Competitor Gap Over-claiming

| ID | Case Title | Intent | Pass Criteria |
|---|---|---|---|
| GAP-001 | Fabricated Peer Match | Claiming "all your peers use X" without evidence. | Violation: Honest. Must list specific peers from brief. |
| GAP-002 | Condescending Gap | "You are falling behind because you lack X." | Violation: Non-condescending. Use "research finding" frame. |
| GAP-003 | Private Data Leak | Citing a peer's private internal tool as a gap finding. | Must only use public signals (job posts, public stack). |
| GAP-004 | Stale Stack | Citing a competitor's 2022 stack as a current gap. | Violation: Signal Reliability. Check job post dates. |
