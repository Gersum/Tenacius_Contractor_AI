from __future__ import annotations

from pathlib import Path

from agent.models.schemas import (
    Channel,
    EmailDeliveryResult,
    InboundMessage,
    LeadRecord,
    MessageDraft,
)
from agent.utils.serialization import write_json


class EmailHandler:
    """Safe email adapter that writes outbound and inbound artifacts locally."""

    def __init__(self, runtime_dir: Path, provider_name: str, sink_mode: bool) -> None:
        self.runtime_dir = runtime_dir / "email"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.provider_name = provider_name
        self.sink_mode = sink_mode

    def send(self, lead: LeadRecord, draft: MessageDraft) -> EmailDeliveryResult:
        result = EmailDeliveryResult(
            delivery_id=f"email_{lead.lead_id}",
            to_address=lead.synthetic_contact_email,
            provider=self.provider_name,
            status="sent_to_sink" if self.sink_mode else "sent",
            sink_mode=self.sink_mode,
            preview_ref=str(self.runtime_dir / f"{lead.lead_id}_outbound.json"),
            subject=draft.subject,
            body=draft.body,
        )
        write_json(Path(result.preview_ref), result)
        return result

    def simulate_reply(self, lead: LeadRecord) -> InboundMessage:
        reply = InboundMessage(
            channel=Channel.EMAIL,
            sender=lead.synthetic_contact_email,
            recipient="sales@tenacious.example",
            body=(
                "This is interesting. We may need Python and data engineering support soon. "
                "If you have a couple of times next week, text them to me and we can confirm there."
            ),
        )
        write_json(self.runtime_dir / f"{lead.lead_id}_reply.json", reply)
        return reply
