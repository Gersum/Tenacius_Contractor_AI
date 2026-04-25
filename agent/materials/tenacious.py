from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from agent.models.schemas import (
    CalendarBooking,
    CompetitorGapBrief,
    ConfidenceLevel,
    ConversationState,
    GapFinding,
    HiringSignalBrief,
    ICPSegment,
    LeadRecord,
    QualificationDecision,
    ScoredSignal,
    SourceRef,
    InboundMessage,
)


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _confidence_from_float(value: float) -> ConfidenceLevel:
    if value >= 0.75:
        return ConfidenceLevel.HIGH
    if value >= 0.45:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _confidence_from_str(value: str) -> ConfidenceLevel:
    normalized = value.strip().lower()
    if normalized == "high":
        return ConfidenceLevel.HIGH
    if normalized == "medium":
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _segment_from_sample(value: str) -> ICPSegment:
    mapping = {
        "segment_1_series_a_b": ICPSegment.RECENTLY_FUNDED,
        "segment_2_mid_market_restructure": ICPSegment.COST_RESTRUCTURING,
        "segment_3_leadership_transition": ICPSegment.LEADERSHIP_TRANSITION,
        "segment_4_specialized_capability": ICPSegment.CAPABILITY_GAP,
    }
    return mapping.get(value, ICPSegment.UNKNOWN)


@dataclass(frozen=True)
class EmailPromptMaterial:
    style_guide: str
    cold_sequence: str
    warm_sequence: str
    reengagement_sequence: str
    pricing_sheet: str
    icp_definition: str
    case_studies: str
    bench_summary: dict[str, Any]
    baseline_numbers: str
    discovery_context_template: str


class TenaciousSalesMaterials:
    """Load the attached Tenacious bundle into structured prompt and seed helpers."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.data_root = project_root / "data" / "tenacious_sales_data"

    def has_seed_for(self, lead: LeadRecord) -> bool:
        sample = self._sample_hiring_signal
        return _normalize(sample["prospect_domain"]) == _normalize(lead.domain)

    def build_seed_hiring_signal_brief(self, lead: LeadRecord, layoff_signal: ScoredSignal) -> HiringSignalBrief:
        sample = self._sample_hiring_signal
        ai_maturity = sample["ai_maturity"]
        funding_event = sample["buying_window_signals"]["funding_event"]
        hiring_velocity = sample["hiring_velocity"]
        leadership_change = sample["buying_window_signals"]["leadership_change"]
        justifications = ai_maturity.get("justifications", [])
        ai_roles_url = next(
            (
                item.get("source_url")
                for item in justifications
                if item.get("signal") == "ai_adjacent_open_roles" and item.get("source_url")
            ),
            f"https://builtin.com/company/{_normalize(lead.company_name).replace(' ', '-')}/jobs",
        )
        leadership_url = next(
            (
                item.get("source_url")
                for item in justifications
                if item.get("signal") == "named_ai_ml_leadership" and item.get("source_url")
            ),
            f"https://{lead.domain}/team",
        )

        funding_source = self._source_ref(
            title="Crunchbase funding round",
            url=funding_event["source_url"],
            note="Seeded Tenacious sample brief.",
        )
        jobs_source = self._source_ref(
            title="BuiltIn jobs",
            url=ai_roles_url,
            note="Seeded Tenacious sample brief.",
        )
        leadership_source = self._source_ref(
            title="Company team page",
            url=leadership_url,
            note="Seeded Tenacious sample brief.",
        )
        source_refs = [funding_source, jobs_source, leadership_source, *layoff_signal.source_refs]

        return HiringSignalBrief(
            company_name=lead.company_name,
            crunchbase_ref=f"https://www.crunchbase.com/organization/{_normalize(lead.company_name).replace(' ', '-')}",
            segment_recommendation=_segment_from_sample(sample["primary_segment_match"]),
            segment_confidence=_confidence_from_float(float(sample["segment_confidence"])),
            funding_signal=ScoredSignal(
                name="recent_funding",
                value=(
                    f"Series {funding_event['stage'].split('_')[-1].upper()} funding closed "
                    f"{funding_event['closed_at']} for ${funding_event['amount_usd']:,}"
                ),
                confidence=ConfidenceLevel.HIGH,
                evidence=[
                    "Seeded prospect profile from attached Tenacious sales materials.",
                    "Funding event is represented in the provided sample hiring brief.",
                ],
                source_refs=[funding_source],
                freshness_days=None,
            ),
            job_post_signal=ScoredSignal(
                name="job_post_velocity",
                value=(
                    f"{hiring_velocity['open_roles_today']} open roles today vs "
                    f"{hiring_velocity['open_roles_60_days_ago']} sixty days ago ({hiring_velocity['velocity_label']})."
                ),
                confidence=_confidence_from_float(float(hiring_velocity["signal_confidence"])),
                evidence=[
                    "Seeded prospect profile from attached Tenacious sales materials.",
                    "Job-post velocity is represented in the provided sample hiring brief.",
                ],
                source_refs=[jobs_source],
            ),
            layoff_signal=layoff_signal,
            leadership_change_signal=ScoredSignal(
                name="leadership_change",
                value="No public leadership change detected in the seeded prospect profile.",
                confidence=ConfidenceLevel.LOW if not leadership_change.get("detected") else ConfidenceLevel.HIGH,
                evidence=[
                    "Seeded prospect profile from attached Tenacious sales materials.",
                    "The sample hiring brief records no leadership change event.",
                ],
                source_refs=[leadership_source],
            ),
            ai_maturity_score=int(ai_maturity["score"]),
            bench_match_summary=self._bench_match_summary(sample),
            ai_maturity_reasoning=[
                f"{item['signal']}: {item['status']}" for item in justifications
            ],
            source_refs=source_refs,
        )

    def build_seed_competitor_gap_brief(self, lead: LeadRecord) -> CompetitorGapBrief:
        sample = self._sample_competitor_gap
        hiring_sample_path = (self.data_root / "schemas" / "sample_hiring_signal_brief.json").resolve()
        competitor_sample_path = (self.data_root / "schemas" / "sample_competitor_gap_brief.json").resolve()
        source_refs = [
            self._source_ref(title="Seed hiring signal brief", url=hiring_sample_path.as_uri(), note="Attached sample brief."),
            self._source_ref(title="Seed competitor gap brief", url=competitor_sample_path.as_uri(), note="Attached sample brief."),
        ]
        gap_findings = [
            GapFinding(
                title=item["practice"],
                description=item["prospect_state"],
                confidence=_confidence_from_str(item["confidence"]),
            )
            for item in sample.get("gap_findings", [])
        ]
        return CompetitorGapBrief(
            company_name=lead.company_name,
            sector=sample["prospect_sector"],
            peer_group_definition=f"{sample['prospect_sub_niche']} against a top-quartile benchmark of {sample['sector_top_quartile_benchmark']}",
            prospect_position_summary=(
                "The prospect matches the sample's AI-augmented BI profile and sits below the top-quartile benchmark."
            ),
            recommended_hook=sample["suggested_pitch_shift"],
            confidence=ConfidenceLevel.HIGH,
            top_quartile_companies=[peer["name"] for peer in sample["competitors_analyzed"] if peer.get("top_quartile")],
            gap_findings=gap_findings,
            source_refs=source_refs,
        )

    def build_reference_competitor_gap_brief(
        self,
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
    ) -> CompetitorGapBrief:
        sample = self._sample_competitor_gap
        competitors = [
            competitor
            for competitor in sample["competitors_analyzed"]
            if _normalize(competitor["domain"]) != _normalize(lead.domain)
        ]
        top_quartile = [competitor for competitor in competitors if competitor.get("top_quartile")]
        benchmark = sample.get("sector_top_quartile_benchmark", 2.75)
        prospect_score = hiring_signal_brief.ai_maturity_score
        gap_delta = round(float(benchmark) - prospect_score, 2)

        source_refs: list[SourceRef] = []
        for competitor in competitors:
            for index, url in enumerate(competitor.get("sources_checked", []), start=1):
                source_refs.append(
                    self._source_ref(
                        title=f"Peer signal: {competitor['name']} source {index}",
                        url=url,
                        note="Attached sector-benchmark competitor sample.",
                    )
                )

        dynamic_gap_findings = self._reference_gap_findings(sample, lead, hiring_signal_brief)
        recommended_hook = (
            dynamic_gap_findings[0].description
            if dynamic_gap_findings
            else "Peer benchmark suggests a research-led outreach angle, but confidence is still exploratory."
        )
        position_summary = (
            f"Prospect AI maturity is {prospect_score}/3 against a reference top-quartile benchmark of {benchmark}. "
            f"Current visible gap delta is {gap_delta}."
        )

        return CompetitorGapBrief(
            company_name=lead.company_name,
            sector=sample["prospect_sector"],
            peer_group_definition=(
                f"{sample['prospect_sub_niche']} reference benchmark built from {len(competitors)} peer companies "
                "in the attached Tenacious sample."
            ),
            prospect_position_summary=position_summary,
            recommended_hook=recommended_hook,
            confidence=hiring_signal_brief.segment_confidence,
            top_quartile_companies=[peer["name"] for peer in top_quartile],
            gap_findings=dynamic_gap_findings,
            source_refs=[*hiring_signal_brief.source_refs, *source_refs],
        )

    def prompt_materials(self, lead: LeadRecord, hiring_signal_brief: HiringSignalBrief, competitor_gap_brief: CompetitorGapBrief) -> EmailPromptMaterial:
        return EmailPromptMaterial(
            style_guide=self._load_text("seed/style_guide.md"),
            cold_sequence=self._extract_section("seed/email_sequences/cold.md", "## Email 1"),
            warm_sequence=self._extract_section("seed/email_sequences/warm.md", "## Engaged reply"),
            reengagement_sequence=self._load_text("seed/email_sequences/reengagement.md"),
            pricing_sheet=self._extract_pricing_guardrails(),
            icp_definition=self._extract_segment_guidance(hiring_signal_brief.segment_recommendation, hiring_signal_brief.ai_maturity_score),
            case_studies=self._load_text("seed/case_studies.md"),
            bench_summary=self._load_json("seed/bench_summary.json"),
            baseline_numbers=self._load_text("seed/baseline_numbers.md"),
            discovery_context_template=self._load_text("schemas/discovery_call_context_brief.md"),
        )

    def render_discovery_context_brief(
        self,
        lead: LeadRecord,
        conversation: ConversationState,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
        booking: CalendarBooking,
        qualification: QualificationDecision,
        inbound_reply: InboundMessage,
    ) -> str:
        bench_summary = self._load_json("seed/bench_summary.json")
        required_stacks = self._sample_hiring_signal.get("bench_to_brief_match", {}).get("required_stacks", [])
        availability_lines = []
        for stack in required_stacks:
            stack_info = bench_summary.get("stacks", {}).get(stack, {})
            if isinstance(stack_info, dict):
                availability_lines.append(
                    f"- {stack}: {stack_info.get('available_engineers', 0)} available engineers"
                )
        availability_block = "\n".join(availability_lines) if availability_lines else "- Bench detail not mapped yet."

        segment_name = hiring_signal_brief.segment_recommendation.value
        return (
            "# Discovery Call Context Brief\n\n"
            f"**Prospect:** {lead.synthetic_contact_name} - {lead.company_name}\n"
            f"**Scheduled:** {booking.scheduled_for}\n"
            f"**Delivery lead assigned:** {self._delivery_lead_name()}\n"
            f"**Call length booked:** 30 minutes\n"
            f"**Thread origin:** {conversation.lead_id} - Email reply from {lead.synthetic_contact_email}\n\n"
            "## 1. Segment and confidence\n\n"
            f"- **Primary segment match:** {segment_name}\n"
            f"- **Confidence:** {hiring_signal_brief.segment_confidence.value}\n"
            f"- **Why this segment:** {competitor_gap_brief.prospect_position_summary}\n"
            "- **Abstention risk:** No - the prospect fits the seeded data profile.\n\n"
            "## 2. Key signals\n\n"
            f"- **Funding event:** {hiring_signal_brief.funding_signal.value}\n"
            f"- **Hiring velocity:** {hiring_signal_brief.job_post_signal.value}\n"
            f"- **Layoff event:** {hiring_signal_brief.layoff_signal.value}\n"
            f"- **Leadership change:** {hiring_signal_brief.leadership_change_signal.value}\n"
            f"- **AI maturity score:** {hiring_signal_brief.ai_maturity_score} / 3 (confidence {hiring_signal_brief.segment_confidence.value})\n\n"
            "## 3. Competitor gap findings\n\n"
            + "\n".join(
                f"- {gap.title}: {gap.description}" for gap in competitor_gap_brief.gap_findings
            )
            + "\n\n"
            "## 4. Bench-to-brief match\n\n"
            f"- **Stacks the prospect will likely need:** {', '.join(required_stacks) if required_stacks else 'python, data'}\n"
            f"- **Available engineers per stack:**\n{availability_block}\n"
            "- **Gaps:** none recorded in the seeded brief\n\n"
            "## 5. Conversation history summary\n\n"
            f"1. Reply body: {inbound_reply.body}\n"
            "2. Prospect is warm and asked for times next week.\n"
            f"3. Qualification result: {qualification.status}.\n\n"
            "## 6. Commercial signals\n\n"
            f"- **Price bands already quoted:** See attached Tenacious pricing sheet\n"
            f"- **Has the prospect asked for a specific total contract value?** No\n"
            f"- **Is the prospect comparing vendors?** Not yet\n"
            f"- **Urgency signals:** Warm reply and booking requested\n\n"
            "## 7. Suggested call structure\n\n"
            "- Minutes 0-2: confirm the signal and the exact need\n"
            "- Minutes 2-10: isolate recruiting velocity or capability gap\n"
            "- Minutes 10-20: confirm bench-to-brief fit\n"
            "- Minutes 20-25: frame the commercial band and next step\n"
            "- Minutes 25-30: confirm proposal path or close the loop\n\n"
            "## 8. What NOT to do\n\n"
            "- Do not over-commit bench capacity.\n"
            "- Do not improvise a total contract value.\n\n"
            "## 9. Agent confidence and unknowns\n\n"
            f"- **Things the agent is confident about:** {competitor_gap_brief.recommended_hook}\n"
            "- **Things the agent is uncertain about:** Any capacity beyond the published bench summary.\n"
            "- **Things the agent could not find:** Live provider round-trips for CRM/calendar in this interim build.\n"
            "- **Overall agent confidence in this brief:** 0.82\n"
        )

    def _extract_segment_guidance(self, segment: ICPSegment, ai_maturity_score: int) -> str:
        text = self._load_text("seed/icp_definition.md")
        segment_heading = {
            ICPSegment.RECENTLY_FUNDED: "## Segment 1",
            ICPSegment.COST_RESTRUCTURING: "## Segment 2",
            ICPSegment.LEADERSHIP_TRANSITION: "## Segment 3",
            ICPSegment.CAPABILITY_GAP: "## Segment 4",
        }.get(segment)
        if not segment_heading:
            return text[:1800]
        block = self._extract_section("seed/icp_definition.md", segment_heading)
        if ai_maturity_score >= 2:
            return block
        return block + "\n\nAI-readiness note: use the low-readiness pitch language."

    def _extract_pricing_guardrails(self) -> str:
        text = self._load_text("seed/pricing_sheet.md")
        return self._extract_section_from_text(
            text,
            "## Talent outsourcing",
            ["## Project consulting", "## Training engagements"],
        )

    def _bench_match_summary(self, sample: dict[str, Any]) -> str:
        bench_summary = self._load_json("seed/bench_summary.json")
        required = sample.get("bench_to_brief_match", {}).get("required_stacks", [])
        availability = bench_summary.get("stacks", {})
        parts = []
        for stack in required:
            stack_info = availability.get(stack)
            if isinstance(stack_info, dict):
                parts.append(f"{stack}: {stack_info.get('available_engineers', 0)} available")
        if not parts:
            return "Bench match remains exploratory until the sample stacks are mapped."
        return "Bench match from attached materials: " + "; ".join(parts) + "."

    def _reference_gap_findings(
        self,
        sample: dict[str, Any],
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
    ) -> list[GapFinding]:
        findings: list[GapFinding] = []
        for item in sample.get("gap_findings", [])[:3]:
            practice = item["practice"]
            confidence = _confidence_from_str(item["confidence"])
            company_context = f"{lead.company_name}'s visible public profile"
            if "leadership" in practice.lower():
                description = (
                    f"{company_context} is compared against this benchmark capability. Public signals currently point to "
                    f"{hiring_signal_brief.leadership_change_signal.value.lower()}"
                )
            elif "mlops" in practice.lower() or "platform" in practice.lower():
                description = (
                    f"{company_context} is compared against this benchmark capability. "
                    f"Current hiring signal: {hiring_signal_brief.job_post_signal.value}"
                )
            else:
                description = (
                    f"{company_context} is compared against this benchmark capability. "
                    f"Funding and AI readiness signals currently read as "
                    f"{hiring_signal_brief.funding_signal.confidence.value} and score "
                    f"{hiring_signal_brief.ai_maturity_score}/3."
                )
            findings.append(
                GapFinding(
                    title=practice,
                    description=description,
                    confidence=confidence,
                )
            )
        return findings

    @cached_property
    def _sample_hiring_signal(self) -> dict[str, Any]:
        return self._load_json("schemas/sample_hiring_signal_brief.json")

    @cached_property
    def _sample_competitor_gap(self) -> dict[str, Any]:
        return self._load_json("schemas/sample_competitor_gap_brief.json")

    def _load_text(self, relative_path: str) -> str:
        return (self.data_root / relative_path).read_text(encoding="utf-8")

    def _load_json(self, relative_path: str) -> dict[str, Any]:
        return json.loads(self._load_text(relative_path))

    def _extract_section(self, relative_path: str, heading: str) -> str:
        return self._extract_section_from_text(self._load_text(relative_path), heading)

    def _extract_section_from_text(self, text: str, heading: str, stop_headings: list[str] | None = None) -> str:
        stop_headings = stop_headings or []
        lines = text.splitlines()
        start_index = None
        for index, line in enumerate(lines):
            if line.strip().startswith(heading):
                start_index = index
                break
        if start_index is None:
            return text[:2000]
        collected: list[str] = []
        for line in lines[start_index:]:
            stripped = line.strip()
            if collected and stripped.startswith("#"):
                if any(stripped.startswith(stop) for stop in stop_headings):
                    break
            collected.append(line)
        return "\n".join(collected).strip()

    def _source_ref(self, title: str, url: str, note: str) -> SourceRef:
        return SourceRef(title=title, url=url, note=note)

    def _delivery_lead_name(self) -> str:
        return "Arun" if self._sample_hiring_signal.get("prospect_domain") else "Delivery Lead"
