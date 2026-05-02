from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error, request

from agent.calendar.calcom import CalComBookingClient, CalComBookingError, InvalidCalComWebhookError
from agent.channels.email.handler import (
    EmailDeliveryError,
    EmailHandler,
    MalformedWebhookPayloadError,
)
from agent.channels.sms.handler import (
    MalformedWebhookPayloadError as SmsMalformedWebhookPayloadError,
    SmsDeliveryError,
    SmsHandler,
)
from agent.config import Settings
from agent.crm.hubspot_mcp import HubSpotMCPClient
from agent.enrichment.pipeline import EnrichmentPipeline
from agent.enrichment.public_signals import PublicPageSnapshot, PublicSignalCollector
from agent.models.schemas import (
    CalendarBooking,
    Channel,
    CompetitorGapBrief,
    ConfidenceLevel,
    ConversationState,
    HiringSignalBrief,
    LeadRecord,
    LeadStatus,
    MessageDraft,
    QualificationDecision,
    ScoredSignal,
    SourceRef,
)
from agent.orchestration.pipeline import ConversionEnginePipeline
from agent.traces.logger import JsonlTraceLogger
from eval.tau_bench.runner import TauBenchRunner


class SmokeTests(unittest.TestCase):
    def _sample_lead(self) -> LeadRecord:
        return LeadRecord(
            company_name="Northstar Analytics",
            domain="northstaranalytics.example",
            synthetic_contact_name="Amina Bekele",
            synthetic_contact_email="amina@northstaranalytics.example",
            synthetic_contact_phone="+251911000000",
        )

    def _sample_conversation(self) -> ConversationState:
        return ConversationState(
            lead_id="lead_test",
            channel=Channel.EMAIL,
            stage=LeadStatus.BOOKED,
            qualification_status="qualified",
            booking_status="booked",
        )

    def _sample_hiring_signal_brief(self) -> HiringSignalBrief:
        source_ref = SourceRef(title="Crunchbase funding round", url="https://example.com/funding")
        return HiringSignalBrief(
            company_name="Northstar Analytics",
            crunchbase_ref="https://example.com/crunchbase",
            segment_recommendation=LeadRecord.__dataclass_fields__["icp_segment"].default,
            segment_confidence=ConfidenceLevel.HIGH,
            funding_signal=ScoredSignal(
                name="recent_funding",
                value="Series A funding closed in the last 90 days",
                confidence=ConfidenceLevel.HIGH,
                source_refs=[source_ref],
            ),
            job_post_signal=ScoredSignal(
                name="job_post_velocity",
                value="8 open roles today vs 3 sixty days ago",
                confidence=ConfidenceLevel.HIGH,
                source_refs=[source_ref],
            ),
            layoff_signal=ScoredSignal(
                name="layoffs",
                value="No layoffs.csv match found",
                confidence=ConfidenceLevel.MEDIUM,
                source_refs=[source_ref],
            ),
            leadership_change_signal=ScoredSignal(
                name="leadership_change",
                value="New VP Engineering hired in the last 60 days",
                confidence=ConfidenceLevel.MEDIUM,
                source_refs=[source_ref],
            ),
            ai_maturity_score=2,
            bench_match_summary="python: 7 available; data: 9 available",
            ai_maturity_reasoning=["3 AI-adjacent roles open", "No named Head of AI"],
            source_refs=[source_ref],
        )

    def _sample_competitor_gap_brief(self) -> CompetitorGapBrief:
        source_ref = SourceRef(title="Peer benchmark", url="https://example.com/peer")
        return CompetitorGapBrief(
            company_name="Northstar Analytics",
            sector="analytics",
            peer_group_definition="Series A analytics firms with active hiring",
            prospect_position_summary="Behind top quartile on AI leadership depth",
            recommended_hook="AI leadership gap plus hiring velocity suggests a near-term staffing need.",
            confidence=ConfidenceLevel.MEDIUM,
            source_refs=[source_ref],
        )

    def _sample_qualification(self) -> QualificationDecision:
        return QualificationDecision(
            status="qualified",
            reason="Prospect asked for next steps",
            booking_recommended=True,
            confidence=ConfidenceLevel.HIGH,
        )

    def _sample_booking(self) -> CalendarBooking:
        return CalendarBooking(
            booking_id="booking_123",
            event_type_slug="tenacious-discovery",
            attendee_email="amina@northstaranalytics.example",
            host_email="delivery-lead@example.com",
            scheduled_for="2026-05-02T09:00:00Z",
            booking_url="https://cal.example/book/booking_123",
            preview_ref="/tmp/booking.json",
        )

    def test_pipeline_runs_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings = Settings(
                runtime_artifacts_path=str(temp_path / "runtime"),
                trace_output_path=str(temp_path / "traces" / "agent_trace_log.jsonl"),
                score_output_path=str(temp_path / "eval" / "score_log.json"),
            )
            logger = JsonlTraceLogger(settings.resolved_trace_output_path)
            pipeline = ConversionEnginePipeline(settings=settings, trace_logger=logger)

            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
                synthetic_contact_phone="+251911000000",
            )

            result = pipeline.run_for_prospect(lead)

            self.assertEqual(result.lead.status, LeadStatus.BOOKED)
            self.assertTrue(Path(result.email_delivery.preview_ref).exists())
            self.assertTrue(Path(result.calendar_booking.preview_ref).exists())
            self.assertTrue(Path(result.hubspot_sync.preview_ref).exists())
            self.assertTrue(settings.resolved_trace_output_path.exists())
            trace_rows = [
                json.loads(line)
                for line in settings.resolved_trace_output_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(any(row["outputs_ref"] for row in trace_rows))
            self.assertTrue(all(row["started_at"] <= row["finished_at"] for row in trace_rows))

    def test_seeded_tenacious_materials_drive_orrin_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings = Settings(
                runtime_artifacts_path=str(temp_path / "runtime"),
                trace_output_path=str(temp_path / "traces" / "agent_trace_log.jsonl"),
                score_output_path=str(temp_path / "eval" / "score_log.json"),
                use_seeded_demo_data=True,
            )
            logger = JsonlTraceLogger(settings.resolved_trace_output_path)
            pipeline = ConversionEnginePipeline(settings=settings, trace_logger=logger)

            lead = LeadRecord(
                company_name="Orrin Labs Inc.",
                domain="orrin-labs.example",
                synthetic_contact_name="Elena Park",
                synthetic_contact_email="elena@orrin-labs.example",
                synthetic_contact_phone="+251911000000",
            )

            result = pipeline.run_for_prospect(lead)

            self.assertEqual(result.hiring_signal_brief.segment_recommendation.value, "recently_funded_series_ab")
            self.assertEqual(result.hiring_signal_brief.ai_maturity_score, 2)
            self.assertIn("AI leadership gap", result.competitor_gap_brief.recommended_hook)
            self.assertTrue((temp_path / "runtime" / "discovery" / f"{lead.lead_id}.md").exists())
            discovery_text = (temp_path / "runtime" / "discovery" / f"{lead.lead_id}.md").read_text(encoding="utf-8")
            self.assertIn("Discovery Call Context Brief", discovery_text)
            self.assertIn("Orrin Labs", discovery_text)

    def test_enrichment_pipeline_collects_public_signals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings = Settings(
                runtime_artifacts_path=str(temp_path / "runtime"),
                trace_output_path=str(temp_path / "traces" / "agent_trace_log.jsonl"),
                score_output_path=str(temp_path / "eval" / "score_log.json"),
            )
            pipeline = EnrichmentPipeline(settings=settings)

            lead = LeadRecord(
                company_name="ExampleCo",
                domain="exampleco.com",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@exampleco.com",
            )

            def fake_capture(self, url: str) -> PublicPageSnapshot:
                if "crunchbase.com" in url:
                    return PublicPageSnapshot(
                        url=url,
                        final_url=url,
                        title="ExampleCo - Crunchbase",
                        text="ExampleCo announced a Series B funding round and raised $20M from public investors.",
                    )
                if url.endswith("/careers"):
                    return PublicPageSnapshot(
                        url=url,
                        final_url=url,
                        title="ExampleCo Careers",
                        text="Open roles\nSenior Data Engineer\nProduct Manager\nStaff Software Engineer",
                        link_texts=("Senior Data Engineer", "Product Manager", "Staff Software Engineer"),
                    )
                if url.endswith("/news"):
                    return PublicPageSnapshot(
                        url=url,
                        final_url=url,
                        title="ExampleCo News",
                        text="ExampleCo appointed Priya Rao as CTO and named Jordan Lee as VP of Engineering.",
                    )
                return PublicPageSnapshot(
                    url=url,
                    final_url=url,
                    title="ExampleCo",
                    text="Careers\nNews\nWe are hiring across engineering and product.",
                    links=("https://exampleco.com/careers", "https://exampleco.com/news"),
                    link_texts=("Careers", "News"),
                )

            with patch.object(PublicSignalCollector, "_capture_public_page", new=fake_capture), patch.object(
                PublicSignalCollector, "_search_public_web", return_value=[]
            ):
                brief = pipeline.build_hiring_signal_brief(lead)

            self.assertEqual(brief.funding_signal.confidence, ConfidenceLevel.HIGH)
            self.assertEqual(brief.job_post_signal.confidence, ConfidenceLevel.HIGH)
            self.assertEqual(brief.leadership_change_signal.confidence, ConfidenceLevel.HIGH)
            self.assertIn("Series B", brief.funding_signal.value)
            self.assertIn("Senior Data Engineer", brief.job_post_signal.value)
            self.assertIn("appointed Priya Rao as CTO", brief.leadership_change_signal.value)
            self.assertGreaterEqual(len(brief.source_refs), 4)

    def test_public_signal_collector_uses_search_results_for_funding_when_crunchbase_is_blocked(self) -> None:
        collector = PublicSignalCollector(company_name="ExampleCo", domain="exampleco.com")

        def fake_capture(self, url: str) -> PublicPageSnapshot:
            if "crunchbase.com" in url:
                return PublicPageSnapshot(url=url, final_url=url, title="", text="", blocked=True)
            return PublicPageSnapshot(
                url=url,
                final_url=url,
                title="ExampleCo Funding News",
                text="ExampleCo raised $20M in a Series B funding round to expand its data platform.",
            )

        with patch.object(PublicSignalCollector, "_capture_public_page", new=fake_capture), patch.object(
            PublicSignalCollector,
            "_search_public_web",
            return_value=[("https://news.example.com/exampleco-series-b", "ExampleCo Series B")],
        ):
            signal = collector.collect_crunchbase_signal()

        self.assertEqual(signal.confidence, ConfidenceLevel.MEDIUM)
        self.assertIn("Public web search indicates funding activity", signal.value)
        self.assertTrue(any("news.example.com" in ref.url for ref in signal.source_refs))

    def test_competitor_gap_brief_uses_live_signals_for_non_seeded_lead(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings = Settings(
                runtime_artifacts_path=str(temp_path / "runtime"),
                trace_output_path=str(temp_path / "traces" / "agent_trace_log.jsonl"),
                score_output_path=str(temp_path / "eval" / "score_log.json"),
            )
            pipeline = EnrichmentPipeline(settings=settings)

            lead = LeadRecord(
                company_name="ExampleCo",
                domain="exampleco.com",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@exampleco.com",
            )

            def fake_capture(self, url: str) -> PublicPageSnapshot:
                if "crunchbase.com" in url:
                    return PublicPageSnapshot(
                        url=url,
                        final_url=url,
                        title="ExampleCo - Crunchbase",
                        text="ExampleCo announced a Series B funding round and raised $20M from public investors.",
                    )
                if url.endswith("/careers"):
                    return PublicPageSnapshot(
                        url=url,
                        final_url=url,
                        title="ExampleCo Careers",
                        text="Open roles\nSenior Data Engineer\nProduct Manager\nStaff Software Engineer",
                        link_texts=("Senior Data Engineer", "Product Manager", "Staff Software Engineer"),
                    )
                if url.endswith("/news"):
                    return PublicPageSnapshot(
                        url=url,
                        final_url=url,
                        title="ExampleCo News",
                        text="ExampleCo appointed Priya Rao as CTO and named Jordan Lee as VP of Engineering.",
                    )
                return PublicPageSnapshot(
                    url=url,
                    final_url=url,
                    title="ExampleCo",
                    text="Careers\nNews\nWe are hiring across engineering and product.",
                    links=("https://exampleco.com/careers", "https://exampleco.com/news"),
                    link_texts=("Careers", "News"),
                )

            with patch.object(PublicSignalCollector, "_capture_public_page", new=fake_capture), patch.object(
                PublicSignalCollector, "_search_public_web", return_value=[]
            ):
                hiring_brief = pipeline.build_hiring_signal_brief(lead)
                competitor_brief = pipeline.build_competitor_gap_brief(lead, hiring_brief)

            self.assertEqual(competitor_brief.top_quartile_companies, [])
            self.assertIn("Live mode", competitor_brief.peer_group_definition)
            self.assertIn("ExampleCo", competitor_brief.recommended_hook)
            self.assertNotIn("Orrin", competitor_brief.recommended_hook)
            self.assertEqual(len(competitor_brief.source_refs), len(hiring_brief.source_refs))

    def test_tau_runner_writes_placeholder_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            runner = TauBenchRunner(
                score_output_path=temp_path / "eval" / "score_log.json",
                trace_output_path=temp_path / "eval" / "trace_log.jsonl",
            )

            summaries = runner.write_placeholder_suite()
            self.assertEqual(len(summaries), 2)
            self.assertTrue((temp_path / "eval" / "score_log.json").exists())
            self.assertTrue((temp_path / "eval" / "trace_log.jsonl").exists())

    def test_tau_runner_derives_scores_from_completed_trace_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            trace_path = temp_path / "eval" / "trace_log.jsonl"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            rows = [
                {
                    "agent_cost": 0.01,
                    "domain": "retail",
                    "duration": 10.0,
                    "reward": 1.0,
                    "simulation_id": "sim_1",
                    "task_id": "1",
                    "termination_reason": "user_stop",
                },
                {
                    "agent_cost": 0.03,
                    "domain": "retail",
                    "duration": 20.0,
                    "reward": 0.0,
                    "simulation_id": "sim_2",
                    "task_id": "2",
                    "termination_reason": "user_stop",
                },
            ]
            trace_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            runner = TauBenchRunner(
                score_output_path=temp_path / "eval" / "score_log.json",
                trace_output_path=trace_path,
            )

            summaries = runner.write_score_from_trace_log(reproduction_simulation_count=1)

            self.assertEqual(summaries[0]["run_label"], "dev_baseline")
            self.assertEqual(summaries[0]["pass_at_1"], 0.5)
            self.assertEqual(summaries[1]["run_label"], "reproduction_check")
            self.assertEqual(summaries[1]["evaluated_simulations"], 1)

    def test_hubspot_sync_uses_stub_mode_without_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = HubSpotMCPClient(Path(temp_dir))
            result = client.sync_contact(
                lead=self._sample_lead(),
                conversation=self._sample_conversation(),
                hiring_signal_brief=self._sample_hiring_signal_brief(),
                competitor_gap_brief=self._sample_competitor_gap_brief(),
                qualification=self._sample_qualification(),
                booking=self._sample_booking(),
            )

            self.assertEqual(result.status, "stubbed")
            preview = json.loads(Path(result.preview_ref).read_text(encoding="utf-8"))
            self.assertEqual(preview["mode"], "stub")
            self.assertEqual(preview["result"]["status"], "stubbed")

    def test_hubspot_sync_creates_contact_when_live_credentials_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = HubSpotMCPClient(Path(temp_dir), access_token="token", portal_id="12345")
            responses = [{"results": []}, {"id": "201"}]

            def fake_urlopen(req: request.Request, timeout: int = 0, **kwargs) -> _FakeHTTPResponse:
                self.assertEqual(req.headers["Authorization"], "Bearer token")
                payload = responses.pop(0)
                return _FakeHTTPResponse(payload)

            with patch("agent.crm.hubspot_mcp.request.urlopen", side_effect=fake_urlopen):
                result = client.sync_contact(
                    lead=self._sample_lead(),
                    conversation=self._sample_conversation(),
                    hiring_signal_brief=self._sample_hiring_signal_brief(),
                    competitor_gap_brief=self._sample_competitor_gap_brief(),
                    qualification=self._sample_qualification(),
                    booking=self._sample_booking(),
                )

            self.assertEqual(result.status, "created")
            self.assertEqual(result.record_id, "201")
            preview = json.loads(Path(result.preview_ref).read_text(encoding="utf-8"))
            self.assertEqual(preview["mode"], "live")
            self.assertEqual(preview["portal_id"], "12345")
            self.assertEqual(preview["result"]["status"], "created")

    def test_hubspot_sync_records_failure_when_api_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = HubSpotMCPClient(Path(temp_dir), access_token="token")

            def fake_urlopen(req: request.Request, timeout: int = 0, **kwargs) -> _FakeHTTPResponse:
                raise error.URLError("hubspot unavailable")

            with patch("agent.crm.hubspot_mcp.request.urlopen", side_effect=fake_urlopen):
                result = client.sync_contact(
                    lead=self._sample_lead(),
                    conversation=self._sample_conversation(),
                    hiring_signal_brief=self._sample_hiring_signal_brief(),
                    competitor_gap_brief=self._sample_competitor_gap_brief(),
                    qualification=self._sample_qualification(),
                    booking=self._sample_booking(),
                )

            self.assertEqual(result.status, "failed")
            preview = json.loads(Path(result.preview_ref).read_text(encoding="utf-8"))
            self.assertEqual(preview["result"]["status"], "failed")
            self.assertIn("hubspot unavailable", preview["error"])

    def test_email_handler_routes_inbound_reply_webhook_to_callback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            received_messages = []
            handler = EmailHandler(
                runtime_dir=runtime_dir,
                provider_name="resend_sink",
                sink_mode=True,
                inbound_handler=received_messages.append,
            )

            event = handler.handle_webhook(
                {
                    "type": "email.replied",
                    "message_id": "msg_123",
                    "from_email": "amina@northstaranalytics.example",
                    "to_email": "sales@tenacious.example",
                    "text": "Could you send times for next week?",
                }
            )

            self.assertEqual(event.status, "received")
            self.assertEqual(event.inbound_message.channel, Channel.EMAIL)
            self.assertEqual(len(received_messages), 1)
            self.assertEqual(received_messages[0].body, "Could you send times for next week?")
            self.assertTrue((runtime_dir / "email" / "webhook_msg_123.json").exists())
            self.assertTrue((runtime_dir / "email" / "inbound_msg_123.json").exists())

    def test_email_handler_marks_bounces_without_silent_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            handler = EmailHandler(runtime_dir=runtime_dir, provider_name="resend_sink", sink_mode=True)

            event = handler.handle_webhook(
                {
                    "type": "email.bounced",
                    "message_id": "msg_bounce",
                    "reason": "Mailbox does not exist",
                }
            )

            self.assertEqual(event.status, "bounce")
            self.assertEqual(event.error_message, "Mailbox does not exist")
            self.assertTrue((runtime_dir / "email" / "webhook_msg_bounce.json").exists())

    def test_email_handler_rejects_malformed_webhook_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            handler = EmailHandler(runtime_dir=runtime_dir, provider_name="resend_sink", sink_mode=True)

            with self.assertRaises(MalformedWebhookPayloadError):
                handler.handle_webhook({"message_id": "msg_bad"})

            self.assertTrue((runtime_dir / "email" / "webhook_msg_bad.json").exists())

    def test_email_handler_rejects_invalid_outbound_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            handler = EmailHandler(runtime_dir=runtime_dir, provider_name="resend_sink", sink_mode=True)
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="invalid-email",
            )
            draft = MessageDraft(
                channel=Channel.EMAIL,
                subject="Checking in",
                body="Hello there",
            )

            with self.assertRaises(EmailDeliveryError) as ctx:
                handler.send(lead, draft)

            self.assertEqual(ctx.exception.result.status, "failed")
            self.assertTrue(Path(ctx.exception.result.preview_ref).exists())

    def test_sms_handler_routes_inbound_reply_webhook_to_callback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            received_messages = []
            handler = SmsHandler(
                runtime_dir=runtime_dir,
                provider_name="africas_talking_sink",
                sink_mode=True,
                inbound_handler=received_messages.append,
            )

            event = handler.handle_webhook(
                {
                    "type": "sms.reply",
                    "message_id": "sms_123",
                    "from_number": "+251911000000",
                    "to_number": "+251900000000",
                    "text": "Tuesday afternoon works for me.",
                }
            )

            self.assertEqual(event.status, "received")
            self.assertEqual(event.inbound_message.channel, Channel.SMS)
            self.assertEqual(len(received_messages), 1)
            self.assertEqual(received_messages[0].body, "Tuesday afternoon works for me.")
            self.assertTrue((runtime_dir / "sms" / "webhook_sms_123.json").exists())
            self.assertTrue((runtime_dir / "sms" / "inbound_sms_123.json").exists())

    def test_sms_handler_rejects_invalid_outbound_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            handler = SmsHandler(runtime_dir=runtime_dir, provider_name="africas_talking_sink", sink_mode=True)
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
                synthetic_contact_phone="",
            )

            with self.assertRaises(SmsDeliveryError) as ctx:
                handler.send_scheduling_message(lead, "Confirming your discovery call.")

            self.assertEqual(ctx.exception.result.status, "failed")
            self.assertTrue(Path(ctx.exception.result.preview_ref).exists())

    def test_sms_handler_rejects_malformed_webhook_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            handler = SmsHandler(runtime_dir=runtime_dir, provider_name="africas_talking_sink", sink_mode=True)

            with self.assertRaises(SmsMalformedWebhookPayloadError):
                handler.handle_webhook({"message_id": "sms_bad"})

            self.assertTrue((runtime_dir / "sms" / "webhook_sms_bad.json").exists())

    def test_calcom_client_falls_back_when_api_key_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3000",
                app_base_url="http://127.0.0.1:3000",
                api_base_url="http://127.0.0.1:3003",
                api_key="",
                event_type_slug="tenacious-discovery",
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2026-04-24T11:00:00Z",
                fallback_enabled=True,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
            )

            booking = client.book_discovery_call(lead, "sales@tenacious.example")
            payload = json.loads(Path(booking.preview_ref).read_text(encoding="utf-8"))

            self.assertEqual(booking.mode, "fallback")
            self.assertEqual(booking.status, "simulated")
            self.assertIn("CALCOM_API_KEY not configured", booking.error_message)
            self.assertEqual(payload["booking"]["mode"], "fallback")
            self.assertIn("fallback_reason", payload["metadata"])

    def test_calcom_client_posts_to_self_hosted_api_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3000",
                app_base_url="http://127.0.0.1:3000",
                api_base_url="http://127.0.0.1:3003",
                api_key="cal_test_123",
                event_type_slug="tenacious-discovery",
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2026-04-24T11:00:00Z",
                fallback_enabled=False,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
                synthetic_contact_phone="+251911000000",
            )

            class FakeResponse:
                def __enter__(self) -> "FakeResponse":
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

                def read(self) -> bytes:
                    return json.dumps(
                        {
                            "status": "success",
                            "data": {
                                "uid": "booking_uid_123",
                                "start": "2026-04-24T11:00:00Z",
                                "bookingUrl": "http://127.0.0.1:3000/booking/booking_uid_123",
                            },
                        }
                    ).encode("utf-8")

            with patch("agent.calendar.calcom.request.urlopen", return_value=FakeResponse()) as mocked_urlopen:
                booking = client.book_discovery_call(lead, "sales@tenacious.example")

            sent_request = mocked_urlopen.call_args.args[0]
            headers = {key.lower(): value for key, value in sent_request.header_items()}
            self.assertEqual(sent_request.full_url, "http://127.0.0.1:3003/v2/bookings")
            self.assertEqual(headers["authorization"], "Bearer cal_test_123")
            self.assertEqual(headers["cal-api-version"], "2026-02-25")
            request_body = json.loads(sent_request.data.decode("utf-8"))
            self.assertEqual(request_body["eventTypeSlug"], "tenacious-discovery")
            self.assertEqual(request_body["username"], "demo-host")
            self.assertEqual(request_body["attendee"]["email"], "amina@northstaranalytics.example")
            self.assertEqual(booking.mode, "api")
            self.assertEqual(booking.status, "confirmed")
            self.assertEqual(booking.booking_url, "http://127.0.0.1:3000/booking/booking_uid_123")

    def test_calcom_client_retries_api_prefix_when_primary_booking_route_404s(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3000",
                app_base_url="http://127.0.0.1:3000",
                api_base_url="http://127.0.0.1:3003",
                api_key="cal_test_123",
                event_type_slug="tenacious-discovery",
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2026-04-24T11:00:00Z",
                fallback_enabled=False,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
            )

            class FakeResponse:
                def __enter__(self) -> "FakeResponse":
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

                def read(self) -> bytes:
                    return json.dumps(
                        {
                            "status": "success",
                            "data": {
                                "uid": "booking_uid_456",
                                "start": "2026-04-24T11:00:00Z",
                                "bookingUrl": "http://127.0.0.1:3000/booking/booking_uid_456",
                            },
                        }
                    ).encode("utf-8")

            not_found = error.HTTPError(
                url="http://127.0.0.1:3003/v2/bookings",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=io.BytesIO(b"{\"status\":\"error\"}"),
            )

            with patch(
                "agent.calendar.calcom.request.urlopen",
                side_effect=[not_found, FakeResponse()],
            ) as mocked_urlopen:
                booking = client.book_discovery_call(lead, "sales@tenacious.example")

            first_request = mocked_urlopen.call_args_list[0].args[0]
            second_request = mocked_urlopen.call_args_list[1].args[0]
            self.assertEqual(first_request.full_url, "http://127.0.0.1:3003/v2/bookings")
            self.assertEqual(second_request.full_url, "http://127.0.0.1:3003/api/v2/bookings")
            self.assertEqual(booking.booking_id, "booking_uid_456")

    def test_calcom_client_raises_clear_error_when_api_server_is_unreachable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3000",
                app_base_url="http://127.0.0.1:3000",
                api_base_url="http://127.0.0.1:3003",
                api_key="cal_test_123",
                event_type_slug="tenacious-discovery",
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2026-04-24T11:00:00Z",
                fallback_enabled=False,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
            )

            with patch(
                "agent.calendar.calcom.request.urlopen",
                side_effect=error.URLError("Connection refused"),
            ):
                with self.assertRaises(CalComBookingError) as ctx:
                    client.book_discovery_call(lead, "sales@tenacious.example")

            self.assertIn("API server was unreachable", str(ctx.exception))

    def test_calcom_client_falls_back_to_app_base_when_api_base_is_unreachable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3004",
                app_base_url="http://127.0.0.1:3004",
                api_base_url="http://127.0.0.1:3003",
                api_key="cal_test_123",
                event_type_slug="tenacious-discovery",
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2026-04-24T11:00:00Z",
                fallback_enabled=False,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
            )

            class FakeResponse:
                def __enter__(self) -> "FakeResponse":
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

                def read(self) -> bytes:
                    return json.dumps(
                        {
                            "status": "success",
                            "data": {
                                "uid": "booking_uid_789",
                                "start": "2026-04-24T11:00:00Z",
                                "bookingUrl": "http://127.0.0.1:3004/booking/booking_uid_789",
                            },
                        }
                    ).encode("utf-8")

            with patch(
                "agent.calendar.calcom.request.urlopen",
                side_effect=[
                    error.URLError("Connection refused"),
                    error.URLError("Connection refused"),
                    error.HTTPError(
                        url="http://127.0.0.1:3004/v2/bookings",
                        code=404,
                        msg="Not Found",
                        hdrs=None,
                        fp=io.BytesIO(b"{\"status\":\"error\"}"),
                    ),
                    FakeResponse(),
                ],
            ) as mocked_urlopen:
                booking = client.book_discovery_call(lead, "sales@tenacious.example")

            attempted_urls = [call.args[0].full_url for call in mocked_urlopen.call_args_list]
            self.assertEqual(
                attempted_urls,
                [
                    "http://127.0.0.1:3003/v2/bookings",
                    "http://127.0.0.1:3003/api/v2/bookings",
                    "http://127.0.0.1:3004/v2/bookings",
                    "http://127.0.0.1:3004/api/v2/bookings",
                ],
            )
            self.assertEqual(booking.booking_id, "booking_uid_789")

    def test_calcom_client_falls_back_to_legacy_booking_endpoint_when_api_v2_is_broken(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3004",
                app_base_url="http://127.0.0.1:3004",
                api_base_url="http://127.0.0.1:3003",
                api_key="cal_test_123",
                event_type_slug="30min",
                event_type_id=1,
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2026-04-28T11:00:00Z",
                fallback_enabled=False,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
            )

            class FakeLegacyResponse:
                def __enter__(self) -> "FakeLegacyResponse":
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

                def read(self) -> bytes:
                    return json.dumps(
                        {
                            "uid": "legacy_booking_uid_123",
                            "startTime": "2026-04-28T11:00:00.000Z",
                            "status": "ACCEPTED",
                        }
                    ).encode("utf-8")

            with patch(
                "agent.calendar.calcom.request.urlopen",
                side_effect=[
                    error.URLError("Connection refused"),
                    error.URLError("Connection refused"),
                    error.HTTPError(
                        url="http://127.0.0.1:3004/v2/bookings",
                        code=500,
                        msg="Internal Server Error",
                        hdrs=None,
                        fp=io.BytesIO(b"Internal Server Error"),
                    ),
                    FakeLegacyResponse(),
                ],
            ) as mocked_urlopen:
                booking = client.book_discovery_call(lead, "sales@tenacious.example")

            attempted_urls = [call.args[0].full_url for call in mocked_urlopen.call_args_list]
            self.assertEqual(
                attempted_urls,
                [
                    "http://127.0.0.1:3003/v2/bookings",
                    "http://127.0.0.1:3003/api/v2/bookings",
                    "http://127.0.0.1:3004/v2/bookings",
                    "http://127.0.0.1:3004/api/book/event",
                ],
            )
            legacy_request = mocked_urlopen.call_args_list[-1].args[0]
            legacy_body = json.loads(legacy_request.data.decode("utf-8"))
            self.assertEqual(legacy_body["eventTypeId"], 1)
            self.assertEqual(legacy_body["responses"]["email"], "amina@northstaranalytics.example")
            self.assertEqual(booking.booking_id, "legacy_booking_uid_123")
            self.assertEqual(booking.booking_url, "http://127.0.0.1:3004/booking/legacy_booking_uid_123")

    def test_calcom_client_retries_legacy_booking_with_next_slot_when_first_slot_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3004",
                app_base_url="http://127.0.0.1:3004",
                api_base_url="http://127.0.0.1:3003",
                api_key="cal_test_123",
                event_type_slug="30min",
                event_type_id=1,
                api_version="2026-02-25",
                host_username="demo-host",
                default_start="2027-04-28T12:00:00Z",
                fallback_enabled=False,
            )
            lead = LeadRecord(
                company_name="Northstar Analytics",
                domain="northstaranalytics.example",
                synthetic_contact_name="Amina Bekele",
                synthetic_contact_email="amina@northstaranalytics.example",
            )

            class FakeLegacyResponse:
                def __enter__(self) -> "FakeLegacyResponse":
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

                def read(self) -> bytes:
                    return json.dumps(
                        {
                            "uid": "legacy_booking_uid_retry",
                            "startTime": "2027-04-28T09:00:00.000Z",
                            "status": "ACCEPTED",
                        }
                    ).encode("utf-8")

            with patch(
                "agent.calendar.calcom.request.urlopen",
                side_effect=[
                    error.URLError("Connection refused"),
                    error.URLError("Connection refused"),
                    error.HTTPError(
                        url="http://127.0.0.1:3004/v2/bookings",
                        code=500,
                        msg="Internal Server Error",
                        hdrs=None,
                        fp=io.BytesIO(b"Internal Server Error"),
                    ),
                    error.HTTPError(
                        url="http://127.0.0.1:3004/api/book/event",
                        code=409,
                        msg="Conflict",
                        hdrs=None,
                        fp=io.BytesIO(b'{\"message\":\"no_available_users_found_error\"}'),
                    ),
                    FakeLegacyResponse(),
                ],
            ) as mocked_urlopen:
                booking = client.book_discovery_call(lead, "sales@tenacious.example")

            attempted_urls = [call.args[0].full_url for call in mocked_urlopen.call_args_list]
            self.assertEqual(
                attempted_urls,
                [
                    "http://127.0.0.1:3003/v2/bookings",
                    "http://127.0.0.1:3003/api/v2/bookings",
                    "http://127.0.0.1:3004/v2/bookings",
                    "http://127.0.0.1:3004/api/book/event",
                    "http://127.0.0.1:3004/api/book/event",
                ],
            )
            first_legacy_body = json.loads(mocked_urlopen.call_args_list[3].args[0].data.decode("utf-8"))
            second_legacy_body = json.loads(mocked_urlopen.call_args_list[4].args[0].data.decode("utf-8"))
            self.assertEqual(first_legacy_body["start"], "2027-04-28T12:00:00Z")
            self.assertEqual(second_legacy_body["start"], "2027-04-28T09:00:00Z")
            self.assertEqual(booking.booking_id, "legacy_booking_uid_retry")

    def test_calcom_webhook_validates_secret_and_routes_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            received_events = []
            client = CalComBookingClient(
                runtime_dir=runtime_dir,
                base_url="http://127.0.0.1:3000",
                app_base_url="http://127.0.0.1:3000",
                api_base_url="http://127.0.0.1:3003",
                api_key="",
                event_type_slug="tenacious-discovery",
                api_version="2026-02-25",
                host_username="",
                default_start="2026-04-24T11:00:00Z",
                fallback_enabled=True,
                webhook_secret="topsecret",
                inbound_handler=received_events.append,
            )

            event = client.handle_webhook(
                {"triggerEvent": "BOOKING_CREATED", "bookingUid": "booking_uid_123"},
                signature="topsecret",
            )

            self.assertEqual(event.status, "booked")
            self.assertEqual(len(received_events), 1)
            self.assertTrue((runtime_dir / "calcom" / "webhook_booking_uid_123.json").exists())

            with self.assertRaises(InvalidCalComWebhookError):
                client.handle_webhook(
                    {"triggerEvent": "BOOKING_CANCELLED", "bookingUid": "booking_uid_123"},
                    signature="wrongsecret",
                )


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
