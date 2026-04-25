from __future__ import annotations

from pathlib import Path

from agent.models.schemas import (
    CalendarBooking,
    CompetitorGapBrief,
    ConversationState,
    HiringSignalBrief,
    HubSpotSyncResult,
    LeadRecord,
    QualificationDecision,
    utc_now,
)
from agent.utils.serialization import write_json


class HubSpotMCPClient:
    """Local HubSpot MCP stub that persists contact snapshots to disk."""

    def __init__(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir / "hubspot"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def sync_contact(
        self,
        lead: LeadRecord,
        conversation: ConversationState,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
        qualification: QualificationDecision,
        booking: CalendarBooking,
    ) -> HubSpotSyncResult:
        enriched_at = utc_now()
        result = HubSpotSyncResult(
            record_id=f"hs_{lead.lead_id}",
            status="upserted",
            preview_ref=str(self.runtime_dir / f"{lead.lead_id}.json"),
            fields={
                "company_name": lead.company_name,
                "contact_email": lead.synthetic_contact_email,
                "icp_segment": lead.icp_segment.value,
                "icp_confidence": lead.icp_confidence.value,
                "enrichment_timestamp": enriched_at,
                "conversation_stage": conversation.stage.value,
                "qualification_status": qualification.status,
                "booking_url": booking.booking_url,
                "ai_maturity_score": hiring_signal_brief.ai_maturity_score,
                "ai_maturity_reasoning": hiring_signal_brief.ai_maturity_reasoning,
                "funding_signal": hiring_signal_brief.funding_signal.value,
                "funding_confidence": hiring_signal_brief.funding_signal.confidence.value,
                "job_post_signal": hiring_signal_brief.job_post_signal.value,
                "job_post_confidence": hiring_signal_brief.job_post_signal.confidence.value,
                "layoff_signal": hiring_signal_brief.layoff_signal.value,
                "layoff_confidence": hiring_signal_brief.layoff_signal.confidence.value,
                "leadership_change_signal": hiring_signal_brief.leadership_change_signal.value,
                "leadership_change_confidence": hiring_signal_brief.leadership_change_signal.confidence.value,
                "bench_match_summary": hiring_signal_brief.bench_match_summary,
                "competitor_gap_position": competitor_gap_brief.prospect_position_summary,
                "recommended_hook": competitor_gap_brief.recommended_hook,
                "source_refs": hiring_signal_brief.source_refs + competitor_gap_brief.source_refs,
            },
        )
        write_json(Path(result.preview_ref), result)
        return result
