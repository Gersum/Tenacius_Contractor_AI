from __future__ import annotations

import json

from agent.config import get_settings
from agent.models.schemas import LeadRecord
from agent.orchestration.pipeline import ConversionEnginePipeline
from agent.traces.logger import JsonlTraceLogger


def run_default_pipeline(lead: LeadRecord | None = None) -> dict:
    settings = get_settings()
    trace_logger = JsonlTraceLogger(settings.resolved_trace_output_path, settings=settings)
    pipeline = ConversionEnginePipeline(settings=settings, trace_logger=trace_logger)

    if lead is None:
        lead = LeadRecord(
            company_name="Vercel",
            domain="vercel.com",
            synthetic_contact_name="Alex Morgan",
            synthetic_contact_email="alex.morgan@example.com",
            synthetic_contact_phone="+251911000000",
        )
    result = pipeline.run_for_prospect(lead)

    return {
        "app_name": settings.app_name,
        "outbound_mode": settings.outbound_mode,
        "lead_id": result.lead.lead_id,
        "segment": result.hiring_signal_brief.segment_recommendation.value,
        "trace_ids": result.trace_ids,
        "email_subject": result.outreach_draft.subject,
        "draft_generation_provider": result.outreach_draft.generation_provider,
        "draft_generation_model": result.outreach_draft.generation_model,
        "draft_generation_mode": result.outreach_draft.generation_mode,
        "draft_prompt_version": result.outreach_draft.prompt_version,
        "draft_generation_error": result.outreach_draft.generation_error,
        "email_preview": result.email_delivery.preview_ref,
        "sms_preview": result.sms_delivery.preview_ref if result.sms_delivery else None,
        "hubspot_preview": result.hubspot_sync.preview_ref,
        "booking_preview": result.calendar_booking.preview_ref,
        "agent_trace_log": str(settings.resolved_trace_output_path),
    }


def main() -> None:
    print(json.dumps(run_default_pipeline(), indent=2))


if __name__ == "__main__":
    main()
