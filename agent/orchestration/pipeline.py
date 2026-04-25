from __future__ import annotations

from time import perf_counter

from agent.calendar.calcom import CalComBookingClient
from agent.channels.email.handler import EmailHandler
from agent.channels.sms.handler import SmsHandler
from agent.config import Settings
from agent.crm.hubspot_mcp import HubSpotMCPClient
from agent.enrichment.pipeline import EnrichmentPipeline
from agent.materials.tenacious import TenaciousSalesMaterials
from agent.models.schemas import (
    Channel,
    ConfidenceLevel,
    ConversationState,
    InboundMessage,
    LeadRecord,
    LeadStatus,
    PipelineResult,
    QualificationDecision,
    TraceRecord,
    utc_now,
)
from agent.policies.channel_handoff import should_switch_to_sms
from agent.policies.grounding import GroundingPolicy
from agent.storage.state_store import FileStateStore
from agent.traces.logger import JsonlTraceLogger


class ConversionEnginePipeline:
    """Local end-to-end thin slice for the Tenacious conversion engine."""

    def __init__(self, settings: Settings, trace_logger: JsonlTraceLogger) -> None:
        self.settings = settings
        self.trace_logger = trace_logger
        self.enrichment_pipeline = EnrichmentPipeline(settings=settings)
        self.materials = TenaciousSalesMaterials(settings.project_root)
        self.grounding_policy = GroundingPolicy(settings=settings)
        self.email_handler = EmailHandler(
            runtime_dir=settings.runtime_artifacts_dir,
            provider_name="resend_sink",
            sink_mode=settings.outbound_mode != "live",
        )
        self.sms_handler = SmsHandler(
            runtime_dir=settings.runtime_artifacts_dir,
            provider_name="africas_talking_sink",
            sink_mode=settings.outbound_mode != "live",
        )
        self.hubspot_client = HubSpotMCPClient(settings.runtime_artifacts_dir)
        self.calcom_client = CalComBookingClient(
            runtime_dir=settings.runtime_artifacts_dir,
            base_url=settings.calcom_base_url,
            app_base_url=settings.calcom_app_base_url,
            api_base_url=settings.calcom_api_base_url,
            api_key=settings.calcom_api_key,
            event_type_slug=settings.calcom_event_type_slug or "tenacious-discovery",
            event_type_id=settings.calcom_event_type_id,
            api_version=settings.calcom_api_version,
            host_username=settings.calcom_username,
            default_start=settings.calcom_booking_start,
            fallback_enabled=settings.calcom_fallback_enabled,
            webhook_secret=settings.calcom_webhook_secret,
        )
        self.state_store = FileStateStore(settings.runtime_artifacts_dir, settings.project_root)

    def run_for_prospect(self, lead: LeadRecord) -> PipelineResult:
        trace_ids: list[str] = []
        conversation = self._timed_step(
            lead=lead,
            step_name="initialize_conversation",
            trace_ids=trace_ids,
            fn=self._initialize_conversation,
        )

        hiring_signal_brief = self._timed_step(
            lead=lead,
            step_name="build_hiring_signal_brief",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=self.enrichment_pipeline.build_hiring_signal_brief,
        )
        lead.status = LeadStatus.ENRICHED
        lead.icp_segment = hiring_signal_brief.segment_recommendation
        lead.icp_confidence = hiring_signal_brief.segment_confidence

        competitor_gap_brief = self._timed_step(
            lead=lead,
            step_name="build_competitor_gap_brief",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.enrichment_pipeline.build_competitor_gap_brief(record, hiring_signal_brief),
        )

        brief_paths = self._timed_step(
            lead=lead,
            step_name="persist_briefs",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.state_store.save_briefs(
                record,
                hiring_signal_brief=hiring_signal_brief,
                competitor_gap_brief=competitor_gap_brief,
            ),
        )

        outreach_draft = self._timed_step(
            lead=lead,
            step_name="compose_initial_outreach",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.grounding_policy.compose_email(
                record,
                hiring_signal_brief=hiring_signal_brief,
                competitor_gap_brief=competitor_gap_brief,
            ),
        )
        lead.status = LeadStatus.OUTREACH_READY

        email_delivery = self._timed_step(
            lead=lead,
            step_name="send_email",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.email_handler.send(record, outreach_draft),
        )
        conversation.stage = LeadStatus.OUTREACH_SENT
        lead.status = LeadStatus.OUTREACH_SENT

        inbound_reply = self._timed_step(
            lead=lead,
            step_name="receive_reply",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=self.email_handler.simulate_reply,
        )
        conversation.stage = LeadStatus.REPLIED
        lead.status = LeadStatus.REPLIED
        conversation.turn_count += 1
        conversation.last_message_at = inbound_reply.received_at

        qualification = self._timed_step(
            lead=lead,
            step_name="qualify_reply",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda _: self._qualify_reply(inbound_reply),
        )
        conversation.qualification_status = qualification.status
        conversation.stage = LeadStatus.QUALIFIED if qualification.booking_recommended else LeadStatus.QUALIFYING
        lead.status = conversation.stage

        calendar_booking = self._timed_step(
            lead=lead,
            step_name="book_calcom_meeting",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.calcom_client.book_discovery_call(record, self.settings.default_sdr_email),
        )
        conversation.booking_status = "booked"
        conversation.stage = LeadStatus.BOOKED
        lead.status = LeadStatus.BOOKED

        discovery_context = self._timed_step(
            lead=lead,
            step_name="write_discovery_context_brief",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.state_store.save_discovery_context(
                record,
                self.materials.render_discovery_context_brief(
                    lead=record,
                    conversation=conversation,
                    hiring_signal_brief=hiring_signal_brief,
                    competitor_gap_brief=competitor_gap_brief,
                    booking=calendar_booking,
                    qualification=qualification,
                    inbound_reply=inbound_reply,
                ),
            ),
        )

        sms_delivery = None
        if should_switch_to_sms(inbound_reply):
            sms_delivery = self._timed_step(
                lead=lead,
                step_name="send_sms_schedule_confirmation",
                trace_ids=trace_ids,
                conversation=conversation,
                fn=lambda record: self.sms_handler.send_scheduling_message(
                    record,
                    (
                        f"Hi {record.synthetic_contact_name}, confirming your Tenacious discovery call for "
                        f"{calendar_booking.scheduled_for}. Booking link: {calendar_booking.booking_url}"
                    ),
                ),
            )

        hubspot_sync = self._timed_step(
            lead=lead,
            step_name="sync_hubspot_record",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.hubspot_client.sync_contact(
                lead=record,
                conversation=conversation,
                hiring_signal_brief=hiring_signal_brief,
                competitor_gap_brief=competitor_gap_brief,
                qualification=qualification,
                booking=calendar_booking,
            ),
        )

        state_path = self._timed_step(
            lead=lead,
            step_name="persist_local_state",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.state_store.save(record, conversation),
        )

        self._timed_step(
            lead=lead,
            step_name="write_visualization_manifest",
            trace_ids=trace_ids,
            conversation=conversation,
            fn=lambda record: self.state_store.save_current_run_manifest(
                record,
                artifact_paths={
                    "state": state_path,
                    "email_outbound": email_delivery.preview_ref,
                    "email_reply": str(self.settings.runtime_artifacts_dir / "email" / f"{record.lead_id}_reply.json"),
                    "sms_confirmation": sms_delivery.preview_ref if sms_delivery else None,
                    "hubspot": hubspot_sync.preview_ref,
                    "calcom": calendar_booking.preview_ref,
                    "discovery_context": discovery_context,
                    "hiring_signal": brief_paths["hiring_signal"],
                    "competitor_gap": brief_paths["competitor_gap"],
                    "agent_traces": self.settings.resolved_trace_output_path,
                    "eval_score_log": self.settings.project_root / "eval" / "score_log.json",
                    "eval_trace_log": self.settings.project_root / "eval" / "trace_log.jsonl",
                    "evidence_graph": self.settings.project_root / "evidence_graph.json",
                },
            ),
        )

        return PipelineResult(
            lead=lead,
            hiring_signal_brief=hiring_signal_brief,
            competitor_gap_brief=competitor_gap_brief,
            outreach_draft=outreach_draft,
            conversation=conversation,
            email_delivery=email_delivery,
            qualification=qualification,
            hubspot_sync=hubspot_sync,
            calendar_booking=calendar_booking,
            inbound_reply=inbound_reply,
            sms_delivery=sms_delivery,
            trace_ids=trace_ids,
        )

    def _timed_step(
        self,
        lead: LeadRecord,
        step_name: str,
        trace_ids: list[str],
        fn,
        conversation: ConversationState | None = None,
    ):
        started_at = utc_now()
        started_counter = perf_counter()
        try:
            result = fn(lead)
        except Exception as exc:
            finished_at = utc_now()
            trace = self._build_trace_record(
                lead=lead,
                step_name=step_name,
                conversation=conversation,
                started_at=started_at,
                finished_at=finished_at,
                latency_ms=int((perf_counter() - started_counter) * 1000),
                status="error",
                result=None,
                error=exc,
            )
            trace_ids.append(self.trace_logger.log(trace))
            raise

        finished_at = utc_now()
        trace = self._build_trace_record(
            lead=lead,
            step_name=step_name,
            conversation=conversation,
            started_at=started_at,
            finished_at=finished_at,
            latency_ms=int((perf_counter() - started_counter) * 1000),
            status="ok",
            result=result,
            error=None,
        )
        trace_ids.append(self.trace_logger.log(trace))
        return result

    def _build_trace_record(
        self,
        lead: LeadRecord,
        step_name: str,
        conversation: ConversationState | None,
        started_at,
        finished_at,
        latency_ms: int,
        status: str,
        result,
        error: Exception | None,
    ) -> TraceRecord:
        output_ref = self._output_ref_for_result(result)
        metadata = {
            "status_after_step": lead.status.value,
            "conversation_stage": conversation.stage.value if conversation else None,
            "generation_provider": getattr(result, "generation_provider", None),
            "generation_mode": getattr(result, "generation_mode", None),
            "generation_error": getattr(result, "generation_error", None),
            "result_type": type(result).__name__ if result is not None else None,
        }
        if output_ref:
            metadata["output_ref"] = output_ref
        if error is not None:
            metadata["error_type"] = type(error).__name__
            metadata["error_message"] = str(error)

        return TraceRecord(
            lead_id=lead.lead_id,
            conversation_id=conversation.conversation_id if conversation else None,
            step_name=step_name,
            started_at=started_at,
            finished_at=finished_at,
            latency_ms=latency_ms,
            model_name=getattr(result, "generation_model", None),
            prompt_version=getattr(result, "prompt_version", None),
            cost_usd=float(getattr(result, "generation_cost_usd", 0.0) or 0.0),
            outputs_ref=output_ref,
            source_refs=[lead.domain],
            status=status,
            metadata=metadata,
        )

    def _output_ref_for_result(self, result) -> str | None:
        if result is None:
            return None
        preview_ref = getattr(result, "preview_ref", None)
        if preview_ref:
            return str(preview_ref)
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            refs = [str(value) for value in result.values() if value]
            return ", ".join(refs) if refs else None
        return None

    def _initialize_conversation(self, lead: LeadRecord) -> ConversationState:
        return ConversationState(
            lead_id=lead.lead_id,
            channel=Channel.EMAIL,
            stage=LeadStatus.NEW,
            turn_count=0,
            qualification_status="pending",
            booking_status="not_started",
        )

    def _qualify_reply(self, reply: InboundMessage) -> QualificationDecision:
        reply_text = reply.body.lower()
        booking_recommended = any(keyword in reply_text for keyword in ("interesting", "support", "times next week"))
        return QualificationDecision(
            status="qualified" if booking_recommended else "needs_follow_up",
            reason="Prospect expressed likely need and scheduling intent in the synthetic reply.",
            booking_recommended=booking_recommended,
            confidence=ConfidenceLevel.MEDIUM,
        )
