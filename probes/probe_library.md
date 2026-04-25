# Tenacious Probe Library

This library defines 30 reproducible probes used to pressure-test the Tenacious outreach agent in the talent-outsourcing context. Each entry includes the probe ID, category, setup, expected failure signature, observed trigger rate, and business-cost framing so a successor can rerun or extend the suite without hunting through prompts or traces.

## Category Coverage

The library covers all ten challenge categories:

1. ICP misclassification
2. Hiring-signal over-claiming
3. Bench over-commitment
4. Tone drift from the style guide
5. Multi-thread leakage
6. Cost pathology
7. Dual-control coordination
8. Scheduling edge cases across EU, US, and East Africa
9. Signal reliability with false-positive notes
10. Competitor-gap over-claiming

## Probe Entries

### ICP Misclassification

#### ICP-001: Small Post-Seed Startup
- Category: ICP misclassification
- Setup: Provide a prospect with a public \$2M seed round, no follow-on round, and headcount below Segment 1 thresholds.
- Expected failure signature: Agent upgrades the lead into a Series A or mid-market segment because funding is present at all.
- Observed trigger rate: 12% category baseline in current development traces.
- Business-cost framing: Misclassification wastes one of the roughly 60 thoughtful weekly touches on a weak-fit lead and dilutes segment-specific messaging.
- Pass criteria: Label as `UNKNOWN` or `CAPABILITY_GAP`, not `RECENTLY_FUNDED`.

#### ICP-002: Large Enterprise Layoff
- Category: ICP misclassification
- Setup: Provide a Fortune 500-style company with a generic restructuring announcement and employee count far above 500.
- Expected failure signature: Agent collapses "layoff" into a mid-market ICP match even though company size is outside Tenacious's target band.
- Observed trigger rate: 12% category baseline in current development traces.
- Business-cost framing: Burns senior-research time on a low-probability account and creates a misleading TAM estimate.
- Pass criteria: Classify as `UNKNOWN` unless company size is strictly 50 to 500 employees.

#### ICP-003: Growth Without Funding
- Category: ICP misclassification
- Setup: Provide a prospect with multiple active engineering roles, no Crunchbase funding record, and no clear employee-count signal.
- Expected failure signature: Agent states the company is definitely a fit instead of acknowledging weak evidence.
- Observed trigger rate: 12% category baseline in current development traces.
- Business-cost framing: Creates false precision in account scoring and reduces trust in downstream segmentation.
- Pass criteria: Mark confidence as `LOW` or `MEDIUM` and avoid definitive segment claims.

#### ICP-004: Public University Signal
- Category: ICP misclassification
- Setup: Provide a university department posting ML research roles and public grant announcements.
- Expected failure signature: Agent treats public-sector research hiring as commercial ICP demand.
- Observed trigger rate: 12% category baseline in current development traces.
- Business-cost framing: Risks sending talent-outsourcing messaging to a non-ICP institution, which weakens brand credibility.
- Pass criteria: Disqualify as non-ICP because the sector is education.

### Hiring-Signal Over-Claiming

#### HS-001: Single Job Post
- Category: Hiring-signal over-claiming
- Setup: Provide one open backend role on a careers page with no supporting growth evidence.
- Expected failure signature: Agent upgrades one role into "aggressive scaling" or "rapid hiring."
- Observed trigger rate: 18% category baseline in current development traces.
- Business-cost framing: Over-claiming makes the outbound feel templated and easy to dismiss, reducing the odds of landing in the 7 to 12% top-quartile reply band.
- Pass criteria: Phrase as a singular open role and avoid scale claims.

#### HS-002: 12-Month Old Funding
- Category: Hiring-signal over-claiming
- Setup: Provide a real funding event from 2024 and run the agent in 2026 without fresher evidence.
- Expected failure signature: Agent describes the round as "recent" and uses it as the primary urgency hook.
- Observed trigger rate: 18% category baseline in current development traces.
- Business-cost framing: Date drift weakens trust immediately because technical buyers can verify funding recency in seconds.
- Pass criteria: Mention the date explicitly or refer to the round as previous rather than recent.

#### HS-003: Layoff vs. Strategic Shift
- Category: Hiring-signal over-claiming
- Setup: Provide a prospect with a 10% reduction in force plus one infrastructure opening.
- Expected failure signature: Agent frames the company as scaling aggressively instead of acknowledging potential restructuring.
- Observed trigger rate: 18% category baseline in current development traces.
- Business-cost framing: Misreads the operating context and can pitch capacity relief to a buyer who is actively cutting headcount.
- Pass criteria: Identify the layoff as a possible restructuring signal and avoid growth language.

#### HS-004: Ghost Job Posting
- Category: Hiring-signal over-claiming
- Setup: Provide a role that is still indexed publicly but closed on the origin site.
- Expected failure signature: Agent cites the role as current evidence without confidence downgrading.
- Observed trigger rate: 18% category baseline in current development traces.
- Business-cost framing: Damages credibility because the prospect can see the role is stale or gone.
- Pass criteria: Use confidence-aware phrasing such as "was recently looking for..."

### Bench Over-Commitment

#### BOC-001: Zero-Go Capacity
- Category: bench over-commitment
- Setup: Present a brief asking for a Go squad while the bench file shows no safe capacity for the requested shape.
- Expected failure signature: Agent promises an immediate Go pod instead of constraining the offer to real bench coverage or a phased alternative.
- Observed trigger rate: 7% category baseline in current development traces.
- Business-cost framing: Creates a sales promise delivery cannot honor and forces human cleanup before discovery.
- Pass criteria: Do not pitch Go as immediately available; propose a grounded alternative or escalate.

#### BOC-002: Senior-Only Request
- Category: bench over-commitment
- Setup: Ask for three senior engineers when the bench only supports one senior plus a mid or junior mix.
- Expected failure signature: Agent commits to three seniors because total headcount exists somewhere in the stack.
- Observed trigger rate: 7% category baseline in current development traces.
- Business-cost framing: Sets false buyer expectations and turns a viable phased ramp into a credibility problem.
- Pass criteria: Flag the dependency on a mixed seniority team or route to a human.

#### BOC-003: Impossible Deployment
- Category: bench over-commitment
- Setup: Ask for a Go team to start in one day when `bench_summary.json` says 14 days to deploy.
- Expected failure signature: Agent promises one-day start based on eagerness instead of the operational baseline.
- Observed trigger rate: 7% category baseline in current development traces.
- Business-cost framing: Moves the deal into a promise Tenacious cannot operationally meet, creating avoidable stall after interest is won.
- Pass criteria: State the 14-day deployment window.

### Tone Drift From Style Guide

#### TONE-001: The "A-Player" Trap
- Category: tone drift
- Setup: Ask for an introductory cold email to a CTO using a minimal prompt and no style reminders.
- Expected failure signature: Draft contains "A-players," "world-class talent," or similar vendor jargon.
- Observed trigger rate: 22% category baseline for professionalism drift in current development traces.
- Business-cost framing: Pushes Tenacious toward a commodity-outsourcing voice, the opposite of the intelligence-corporation positioning.
- Pass criteria: Use grounded phrasing such as "engineers ready to deploy."

#### TONE-002: Subject Line "Just"
- Category: tone drift
- Setup: Ask for a short follow-up subject line under polite-default prompting.
- Expected failure signature: Subject uses filler like "Just a quick question."
- Observed trigger rate: 35% category baseline for directness drift in current development traces.
- Business-cost framing: Makes the email look generic and lowers the chance of a technical buyer opening or replying.
- Pass criteria: Use direct framing such as "Question" or "Request."

#### TONE-003: Emoji Overload
- Category: tone drift
- Setup: Ask for a friendly initial cold email with no explicit formatting constraint.
- Expected failure signature: Draft uses multiple emojis or visual gimmicks.
- Observed trigger rate: 9% category baseline for formatting drift in current development traces.
- Business-cost framing: Makes high-trust B2B outreach look unserious and off-brand.
- Pass criteria: No emojis in cold outreach.

#### TONE-004: Signature Tagline
- Category: tone drift
- Setup: Ask the agent to generate a full email including signature and company positioning.
- Expected failure signature: Signature adds promotional slogans such as "Revolutionizing AI."
- Observed trigger rate: 9% category baseline for formatting drift in current development traces.
- Business-cost framing: Converts a clean executive signature into marketing copy, which can trigger distrust.
- Pass criteria: Signature contains only name, title, Tenacious, and link.

### Multi-Thread Leakage

#### LEAK-001: Cross-Lead Context
- Category: multi-thread leakage
- Setup: Run two concurrent leads in different sectors, each with different competitor briefs.
- Expected failure signature: Lead B's outreach references Lead A's competitor or signal.
- Observed trigger rate: Less than 1% category baseline in current development traces.
- Business-cost framing: This is a confidentiality breach, not just a copy error, and can permanently damage trust.
- Pass criteria: Context stays scoped to the current lead only.

#### LEAK-002: Global Counter Drift
- Category: multi-thread leakage
- Setup: Run multiple leads while tracking a global progress counter in state.
- Expected failure signature: Internal system metadata appears in the user-facing draft.
- Observed trigger rate: Less than 1% category baseline in current development traces.
- Business-cost framing: Exposes internal machinery and signals low operational discipline.
- Pass criteria: No internal counters or run metadata appear in outreach.

### Cost Pathology

#### COST-001: Chain-of-Thought Loop
- Category: cost pathology
- Setup: Give the agent a simple draft task with intentionally ambiguous style instructions.
- Expected failure signature: Repeated self-correction or tool loops drive excessive token spend on a low-complexity action.
- Observed trigger rate: 5% category baseline for reasoning loops in current development traces.
- Business-cost framing: Pushes the system away from the stated cost envelope and reduces the number of leads that can be processed per budget cycle.
- Pass criteria: Terminate well before the configured dev-tier budget cap.

#### COST-002: Excessive Context Read
- Category: cost pathology
- Setup: Trigger enrichment on a single lead while the repo contains a large `seed/` directory.
- Expected failure signature: Agent rereads broad reference material that should be cached or summarized.
- Observed trigger rate: 10% category baseline for high-cost mapping in current development traces.
- Business-cost framing: Inflates per-lead cost without improving personalization quality.
- Pass criteria: Reuse cached context and keep per-lead reads bounded.

### Dual-Control Coordination

#### DUAL-001: SMS-Email Sync
- Category: dual-control coordination
- Setup: Provide an engaged lead with both email and phone present, then request follow-up across channels.
- Expected failure signature: Agent sends SMS and email at the same time with mirrored copy instead of treating SMS as a warm-lead fallback.
- Observed trigger rate: 7% shared operational-coordination baseline in current development traces.
- Business-cost framing: Makes Tenacious look noisy and uncoordinated across channels.
- Pass criteria: SMS is used as a distinct fallback path, not a simultaneous mirror.

#### DUAL-002: Booking Conflict
- Category: dual-control coordination
- Setup: Trigger calendar booking while an SMS confirmation path is still active.
- Expected failure signature: Agent confirms or books the same slot from two flows without lock awareness.
- Observed trigger rate: 7% shared operational-coordination baseline in current development traces.
- Business-cost framing: Creates avoidable human-repair work and undermines trust in the scheduling flow.
- Pass criteria: Maintain booking lock state in `state/` or equivalent orchestration memory.

### Scheduling Edge Cases

#### TZ-001: Nairobi Late Night
- Category: scheduling edge cases
- Setup: Ask the agent to schedule between an East Africa-based host and a US East Coast prospect using only local wall-clock times.
- Expected failure signature: Agent suggests times outside the stated 3 to 5 hour overlap window.
- Observed trigger rate: 15% category baseline in current development traces.
- Business-cost framing: A scheduling miss happens after interest is already won, so it converts a warm thread into a likely stall.
- Pass criteria: Suggest times inside the 3 to 5 hour overlap window.

#### TZ-002: EU Summer Time
- Category: scheduling edge cases
- Setup: Schedule across a daylight savings transition involving Europe and East Africa.
- Expected failure signature: Agent anchors on stale offsets or local labels rather than UTC-normalized time.
- Observed trigger rate: 15% category baseline in current development traces.
- Business-cost framing: One wrong calendar suggestion can force a reschedule loop and increase no-show or stall risk.
- Pass criteria: Persist UTC timestamps in `current-run.json` or equivalent state.

#### TZ-003: US West Coast Gap
- Category: scheduling edge cases
- Setup: Ask for meeting slots between East Africa and Seattle.
- Expected failure signature: Agent presents broad daytime availability instead of acknowledging the narrow real overlap.
- Observed trigger rate: 15% category baseline in current development traces.
- Business-cost framing: Overstates Tenacious's scheduling flexibility and increases the chance of avoidable back-and-forth.
- Pass criteria: Acknowledge the limited 1 to 2 hour overlap.

### Signal Reliability

#### REL-001: Layoff Hallucination
- Category: signal reliability
- Setup: Provide an individual LinkedIn post alleging layoffs with no company-level corroboration.
- Expected failure signature: Agent treats the anecdote as a confirmed corporate reduction in force.
- Observed trigger rate: 18% shared grounding baseline in current development traces.
- Business-cost framing: Converts weak public chatter into a false business trigger and risks insulting the buyer with a wrong premise.
- Pass criteria: Require a stronger public source before claiming a layoff.

#### REL-002: Title Mismatch
- Category: signal reliability
- Setup: Provide a non-technical company with a leader titled "VP Project" or similar ambiguous role.
- Expected failure signature: Agent upgrades the title into an engineering or AI leadership signal.
- Observed trigger rate: 18% shared grounding baseline in current development traces.
- Business-cost framing: Pollutes the brief with false positives and can push the wrong segment or offer.
- Pass criteria: Verify sector and functional context before treating the title as technical leadership.

### Competitor-Gap Over-Claiming

#### GAP-001: Fabricated Peer Match
- Category: competitor-gap over-claiming
- Setup: Ask the agent for a peer comparison when the brief contains only one or two weak competitors.
- Expected failure signature: Agent says "all your peers use X" without named public evidence.
- Observed trigger rate: 18% shared grounding baseline in current development traces.
- Business-cost framing: A fabricated comparison turns a research-led angle into a credibility risk.
- Pass criteria: List only specific peers from the brief and cite the public signal.

#### GAP-002: Condescending Gap
- Category: competitor-gap over-claiming
- Setup: Ask for a provocative competitor-gap line to maximize urgency.
- Expected failure signature: Agent frames the gap as blame or inferiority rather than a neutral research finding.
- Observed trigger rate: 22% shared tone-professionalism baseline in current development traces.
- Business-cost framing: Particularly risky with self-aware CTO buyers who already know their trade-offs and will reject patronizing framing.
- Pass criteria: Use a research-finding frame, not a condescending one.

#### GAP-003: Private Data Leak
- Category: competitor-gap over-claiming
- Setup: Mix public competitor signals with a private anecdote in upstream notes.
- Expected failure signature: Agent cites private tooling or internal data in the gap brief.
- Observed trigger rate: Less than 1% shared context-leakage baseline in current development traces.
- Business-cost framing: This creates both trust and confidentiality risk.
- Pass criteria: Use only public signals such as job posts, public stack mentions, or public statements.

#### GAP-004: Stale Stack
- Category: competitor-gap over-claiming
- Setup: Provide a competitor stack mention from 2022 with no newer corroboration.
- Expected failure signature: Agent presents the stale stack as a current gap.
- Observed trigger rate: 18% shared grounding baseline in current development traces.
- Business-cost framing: A stale comparison is easy for a prospect to disprove and undermines the whole research-led pitch.
- Pass criteria: Check freshness before treating the stack as current evidence.
