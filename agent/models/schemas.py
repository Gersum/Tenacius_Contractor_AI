from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"


class LeadStatus(str, Enum):
    NEW = "new"
    ENRICHED = "enriched"
    OUTREACH_READY = "outreach_ready"
    OUTREACH_SENT = "outreach_sent"
    REPLIED = "replied"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    BOOKING_PENDING = "booking_pending"
    BOOKED = "booked"
    HANDOFF = "handoff"
    DISQUALIFIED = "disqualified"
    STOPPED = "stopped"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ICPSegment(str, Enum):
    RECENTLY_FUNDED = "recently_funded_series_ab"
    COST_RESTRUCTURING = "mid_market_restructuring"
    LEADERSHIP_TRANSITION = "engineering_leadership_transition"
    CAPABILITY_GAP = "specialized_capability_gap"
    UNKNOWN = "unknown"


@dataclass
class SourceRef:
    title: str
    url: str
    note: str | None = None
    accessed_at: datetime = field(default_factory=utc_now)


@dataclass
class ScoredSignal:
    name: str
    value: str
    confidence: ConfidenceLevel
    evidence: list[str] = field(default_factory=list)
    source_refs: list[SourceRef] = field(default_factory=list)
    freshness_days: int | None = None


@dataclass
class LeadRecord:
    company_name: str
    domain: str
    synthetic_contact_name: str
    synthetic_contact_email: str
    synthetic_contact_phone: str | None = None
    source_type: str = "synthetic"
    icp_segment: ICPSegment = ICPSegment.UNKNOWN
    icp_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    status: LeadStatus = LeadStatus.NEW
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    lead_id: str = field(default_factory=lambda: f"lead_{uuid4().hex[:12]}")


@dataclass
class HiringSignalBrief:
    company_name: str
    crunchbase_ref: str
    segment_recommendation: ICPSegment
    segment_confidence: ConfidenceLevel
    funding_signal: ScoredSignal
    job_post_signal: ScoredSignal
    layoff_signal: ScoredSignal
    leadership_change_signal: ScoredSignal
    ai_maturity_score: int
    bench_match_summary: str
    ai_maturity_reasoning: list[str] = field(default_factory=list)
    source_refs: list[SourceRef] = field(default_factory=list)
    generated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not 0 <= self.ai_maturity_score <= 3:
            raise ValueError("ai_maturity_score must be between 0 and 3.")


@dataclass
class GapFinding:
    title: str
    description: str
    confidence: ConfidenceLevel


@dataclass
class CompetitorGapBrief:
    company_name: str
    sector: str
    peer_group_definition: str
    prospect_position_summary: str
    recommended_hook: str
    confidence: ConfidenceLevel
    top_quartile_companies: list[str] = field(default_factory=list)
    gap_findings: list[GapFinding] = field(default_factory=list)
    source_refs: list[SourceRef] = field(default_factory=list)
    generated_at: datetime = field(default_factory=utc_now)


@dataclass
class MessageDraft:
    channel: Channel
    body: str
    subject: str | None = None
    variant_tag: str = "baseline"
    prompt_version: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source_backed_claims: list[str] = field(default_factory=list)
    generation_provider: str = "local_template"
    generation_model: str | None = None
    generation_mode: str = "template"
    generation_cost_usd: float = 0.0
    generation_error: str | None = None


@dataclass
class InboundMessage:
    channel: Channel
    sender: str
    recipient: str
    body: str
    received_at: datetime = field(default_factory=utc_now)


@dataclass
class ConversationState:
    lead_id: str
    channel: Channel
    stage: LeadStatus = LeadStatus.NEW
    turn_count: int = 0
    qualification_status: str = "unknown"
    booking_status: str = "not_started"
    human_handoff_required: bool = False
    last_message_at: datetime | None = None
    conversation_id: str = field(default_factory=lambda: f"conv_{uuid4().hex[:12]}")


@dataclass
class QualificationDecision:
    status: str
    reason: str
    booking_recommended: bool
    confidence: ConfidenceLevel


@dataclass
class EmailDeliveryResult:
    delivery_id: str
    to_address: str
    provider: str
    status: str
    sink_mode: bool
    body: str
    preview_ref: str
    subject: str | None = None
    sent_at: datetime = field(default_factory=utc_now)


@dataclass
class EmailWebhookEvent:
    provider: str
    event_type: str
    status: str
    message_id: str | None = None
    payload_ref: str | None = None
    error_message: str | None = None
    inbound_message: InboundMessage | None = None
    received_at: datetime = field(default_factory=utc_now)


@dataclass
class SmsWebhookEvent:
    provider: str
    event_type: str
    status: str
    message_id: str | None = None
    payload_ref: str | None = None
    error_message: str | None = None
    inbound_message: InboundMessage | None = None
    received_at: datetime = field(default_factory=utc_now)


@dataclass
class SmsDeliveryResult:
    delivery_id: str
    to_number: str
    provider: str
    status: str
    sink_mode: bool
    body: str
    preview_ref: str
    sent_at: datetime = field(default_factory=utc_now)


@dataclass
class HubSpotSyncResult:
    record_id: str
    status: str
    preview_ref: str
    fields: dict[str, Any] = field(default_factory=dict)
    synced_at: datetime = field(default_factory=utc_now)


@dataclass
class CalendarBooking:
    booking_id: str
    event_type_slug: str
    attendee_email: str
    host_email: str
    scheduled_for: str
    booking_url: str
    preview_ref: str
    provider: str = "cal.com"
    mode: str = "stub"
    status: str = "confirmed"
    host_username: str | None = None
    raw_response_ref: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class CalendarWebhookEvent:
    provider: str
    event_type: str
    status: str
    booking_id: str | None = None
    payload_ref: str | None = None
    error_message: str | None = None
    received_at: datetime = field(default_factory=utc_now)


@dataclass
class TraceRecord:
    lead_id: str
    step_name: str
    conversation_id: str | None = None
    started_at: datetime = field(default_factory=utc_now)
    finished_at: datetime = field(default_factory=utc_now)
    latency_ms: int = 0
    model_name: str | None = None
    prompt_version: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    inputs_ref: str | None = None
    outputs_ref: str | None = None
    source_refs: list[str] = field(default_factory=list)
    status: str = "ok"
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: f"tr_{uuid4().hex[:12]}")


@dataclass
class PipelineResult:
    lead: LeadRecord
    hiring_signal_brief: HiringSignalBrief
    competitor_gap_brief: CompetitorGapBrief
    outreach_draft: MessageDraft
    conversation: ConversationState
    email_delivery: EmailDeliveryResult
    qualification: QualificationDecision
    hubspot_sync: HubSpotSyncResult
    calendar_booking: CalendarBooking
    inbound_reply: InboundMessage
    sms_delivery: SmsDeliveryResult | None = None
    trace_ids: list[str] = field(default_factory=list)
