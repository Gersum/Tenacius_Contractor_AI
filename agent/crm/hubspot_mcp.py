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
        result = HubSpotSyncResult(
            record_id=f"hs_{lead.lead_id}",
            status="upserted",
            preview_ref=str(self.runtime_dir / f"{lead.lead_id}.json"),
            fields={
                "company_name": lead.company_name,
                "contact_email": lead.synthetic_contact_email,
                "icp_segment": lead.icp_segment.value,
                "conversation_stage": conversation.stage.value,
                "qualification_status": qualification.status,
                "booking_url": booking.booking_url,
                "ai_maturity_score": hiring_signal_brief.ai_maturity_score,
                "recommended_hook": competitor_gap_brief.recommended_hook,
            },
        )
        write_json(Path(result.preview_ref), result)
        return result
