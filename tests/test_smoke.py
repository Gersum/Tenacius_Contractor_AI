from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.channels.email.handler import (
    EmailDeliveryError,
    EmailHandler,
    MalformedWebhookPayloadError,
)
from agent.config import Settings
from agent.models.schemas import Channel, LeadRecord, LeadStatus, MessageDraft
from agent.orchestration.pipeline import ConversionEnginePipeline
from agent.traces.logger import JsonlTraceLogger
from eval.tau_bench.runner import TauBenchRunner


class SmokeTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
