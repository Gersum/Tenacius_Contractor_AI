from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.main import run_default_pipeline
from agent.config import get_settings
from agent.calendar.calcom import CalComBookingClient
from agent.models.schemas import LeadRecord
from agent.utils.serialization import to_jsonable
from eval.tau_bench.runner import TauBenchRunner


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class VisualizationRequestHandler(SimpleHTTPRequestHandler):
    """Static visualization server with local operator actions."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            settings = get_settings()
            self._send_json(
                {
                    "status": "ok",
                    "mode": "operator_api",
                    "calcom": {
                        "base_url": settings.calcom_base_url,
                        "app_base_url": settings.calcom_app_base_url,
                        "api_base_url": settings.calcom_api_base_url,
                        "event_type_slug": settings.calcom_event_type_slug,
                        "api_key_configured": bool(settings.calcom_api_key),
                    },
                }
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/run":
            self._handle_run()
            return
        if self.path == "/api/recompute-eval":
            self._handle_recompute_eval()
            return
        if self.path == "/api/calcom-webhook":
            self._handle_calcom_webhook()
            return
        self.send_error(404, "Unknown API route")

    def _handle_run(self) -> None:
        try:
            payload = self._read_json_body()
            lead = self._lead_from_payload(payload)
            result = run_default_pipeline(lead)
            self._send_json({"status": "ok", "result": result})
        except Exception as exc:
            self._send_json(
                {"status": "error", "error_type": type(exc).__name__, "message": str(exc)},
                status=500,
            )

    def _handle_recompute_eval(self) -> None:
        try:
            runner = TauBenchRunner(
                score_output_path=PROJECT_ROOT / "eval" / "score_log.json",
                trace_output_path=PROJECT_ROOT / "eval" / "trace_log.jsonl",
            )
            summaries = runner.write_score_from_trace_log(
                model_name="pinned_dev_tier_model",
                git_commit=runner.existing_git_commit(),
            )
            self._send_json({"status": "ok", "summaries": summaries})
        except Exception as exc:
            self._send_json(
                {"status": "error", "error_type": type(exc).__name__, "message": str(exc)},
                status=500,
            )

    def _handle_calcom_webhook(self) -> None:
        try:
            payload = self._read_json_body()
            settings = get_settings()
            client = CalComBookingClient(
                runtime_dir=settings.runtime_artifacts_dir,
                base_url=settings.calcom_base_url,
                app_base_url=settings.calcom_app_base_url,
                api_base_url=settings.calcom_api_base_url,
                api_key=settings.calcom_api_key,
                event_type_slug=settings.calcom_event_type_slug or "tenacious-discovery",
                api_version=settings.calcom_api_version,
                host_username=settings.calcom_username,
                default_start=settings.calcom_booking_start,
                fallback_enabled=settings.calcom_fallback_enabled,
                webhook_secret=settings.calcom_webhook_secret,
            )
            event = client.handle_webhook(payload, signature=self.headers.get("x-cal-signature"))
            self._send_json({"status": "ok", "event": event})
        except Exception as exc:
            self._send_json(
                {"status": "error", "error_type": type(exc).__name__, "message": str(exc)},
                status=400,
            )

    def _lead_from_payload(self, payload: dict[str, Any]) -> LeadRecord | None:
        lead_payload = payload.get("lead") if isinstance(payload, dict) else None
        if not lead_payload:
            return None
        return LeadRecord(
            company_name=str(lead_payload.get("company_name") or "Vercel"),
            domain=str(lead_payload.get("domain") or "vercel.com"),
            synthetic_contact_name=str(lead_payload.get("synthetic_contact_name") or "Alex Morgan"),
            synthetic_contact_email=str(lead_payload.get("synthetic_contact_email") or "alex.morgan@example.com"),
            synthetic_contact_phone=str(lead_payload.get("synthetic_contact_phone") or "+251911000000"),
        )

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length == 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw_body)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(to_jsonable(payload), indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ReusableThreadingHTTPServer(("127.0.0.1", 8000), VisualizationRequestHandler)
    print("Visualization operator UI running at http://127.0.0.1:8000/visualization/")
    server.serve_forever()


if __name__ == "__main__":
    main()
