from __future__ import annotations

from pathlib import Path

from agent.models.schemas import LeadRecord, SmsDeliveryResult
from agent.utils.serialization import write_json


class SmsHandler:
    """Africa's Talking-style sink adapter for warm-lead scheduling messages."""

    def __init__(self, runtime_dir: Path, provider_name: str, sink_mode: bool) -> None:
        self.runtime_dir = runtime_dir / "sms"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.provider_name = provider_name
        self.sink_mode = sink_mode

    def send_scheduling_message(self, lead: LeadRecord, message: str) -> SmsDeliveryResult:
        result = SmsDeliveryResult(
            delivery_id=f"sms_{lead.lead_id}",
            to_number=lead.synthetic_contact_phone or "unknown",
            provider=self.provider_name,
            status="sent_to_sink" if self.sink_mode else "sent",
            sink_mode=self.sink_mode,
            body=message,
            preview_ref=str(self.runtime_dir / f"{lead.lead_id}_scheduling.json"),
        )
        write_json(Path(result.preview_ref), result)
        return result
