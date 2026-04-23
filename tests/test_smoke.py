from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.config import Settings
from agent.models.schemas import LeadRecord, LeadStatus
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


if __name__ == "__main__":
    unittest.main()
