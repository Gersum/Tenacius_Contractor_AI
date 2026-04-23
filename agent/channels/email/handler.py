from __future__ import annotations

from pathlib import Path
from typing import Callable

from agent.models.schemas import (
    Channel,
    EmailDeliveryResult,
    EmailWebhookEvent,
    InboundMessage,
    LeadRecord,
    MessageDraft,
)
from agent.utils.serialization import write_json


class EmailHandlerError(RuntimeError):
    """Base exception for email handler failures."""


class EmailDeliveryError(EmailHandlerError):
    """Raised when an outbound send cannot be completed safely."""

    def __init__(self, message: str, result: EmailDeliveryResult) -> None:
        super().__init__(message)
        self.result = result


class MalformedWebhookPayloadError(EmailHandlerError):
    """Raised when a provider webhook payload is malformed."""

    def __init__(self, message: str, event: EmailWebhookEvent) -> None:
        super().__init__(message)
        self.event = event


InboundReplyHandler = Callable[[InboundMessage], None]


class EmailHandler:
    """Email adapter with explicit outbound, inbound, and error-path handling."""

    def __init__(
        self,
        runtime_dir: Path,
        provider_name: str,
        sink_mode: bool,
        inbound_handler: InboundReplyHandler | None = None,
    ) -> None:
        self.runtime_dir = runtime_dir / "email"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.provider_name = provider_name
        self.sink_mode = sink_mode
        self.inbound_handler = inbound_handler

    def register_inbound_handler(self, handler: InboundReplyHandler) -> None:
        self.inbound_handler = handler

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

        validation_error = self._validate_outbound(lead, draft)
        if validation_error is not None:
            result.status = "failed"
            write_json(Path(result.preview_ref), result)
            raise EmailDeliveryError(validation_error, result)

        write_json(Path(result.preview_ref), result)
        return result

    def handle_webhook(self, payload: dict, provider_name: str | None = None) -> EmailWebhookEvent:
        provider = provider_name or self.provider_name
        event_type = self._extract_event_type(payload)
        message_id = self._extract_message_id(payload)
        payload_ref = str(self.runtime_dir / f"webhook_{message_id or 'unknown'}.json")

        if event_type is None:
            event = EmailWebhookEvent(
                provider=provider,
                event_type="unknown",
                status="malformed",
                message_id=message_id,
                payload_ref=payload_ref,
                error_message="Missing provider event type in email webhook payload.",
            )
            write_json(Path(payload_ref), {"payload": payload, "event": event})
            raise MalformedWebhookPayloadError(event.error_message, event)

        if event_type in {"email.bounced", "bounced", "bounce"}:
            event = EmailWebhookEvent(
                provider=provider,
                event_type=event_type,
                status="bounce",
                message_id=message_id,
                payload_ref=payload_ref,
                error_message=self._extract_bounce_reason(payload),
            )
            write_json(Path(payload_ref), {"payload": payload, "event": event})
            return event

        if event_type in {"email.replied", "inbound.reply", "reply"}:
            inbound = self._build_inbound_message(payload)
            event = EmailWebhookEvent(
                provider=provider,
                event_type=event_type,
                status="received",
                message_id=message_id,
                payload_ref=payload_ref,
                inbound_message=inbound,
            )
            write_json(Path(payload_ref), {"payload": payload, "event": event})
            write_json(self.runtime_dir / f"inbound_{message_id or 'unknown'}.json", inbound)
            if self.inbound_handler is not None:
                self.inbound_handler(inbound)
            return event

        event = EmailWebhookEvent(
            provider=provider,
            event_type=event_type,
            status="ignored",
            message_id=message_id,
            payload_ref=payload_ref,
            error_message=f"Unhandled email webhook event type: {event_type}",
        )
        write_json(Path(payload_ref), {"payload": payload, "event": event})
        return event

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
        if self.inbound_handler is not None:
            self.inbound_handler(reply)
        return reply

    def _validate_outbound(self, lead: LeadRecord, draft: MessageDraft) -> str | None:
        if "@" not in lead.synthetic_contact_email:
            return "Outbound email send failed: recipient email address is invalid."
        if not draft.subject or not draft.subject.strip():
            return "Outbound email send failed: subject is required."
        if not draft.body.strip():
            return "Outbound email send failed: body is required."
        return None

    def _extract_event_type(self, payload: dict) -> str | None:
        raw = payload.get("type") or payload.get("event")
        if isinstance(raw, str) and raw.strip():
            return raw.strip().lower()
        data = payload.get("data")
        if isinstance(data, dict):
            nested = data.get("type") or data.get("event")
            if isinstance(nested, str) and nested.strip():
                return nested.strip().lower()
        return None

    def _extract_message_id(self, payload: dict) -> str | None:
        for key in ("message_id", "email_id", "id"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("message_id", "email_id", "id"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def _extract_bounce_reason(self, payload: dict) -> str:
        for key in ("reason", "error", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("reason", "error", "message"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return "Email bounced without provider reason."

    def _build_inbound_message(self, payload: dict) -> InboundMessage:
        sender = self._extract_string(payload, "from_email", "from", "sender")
        recipient = self._extract_string(payload, "to_email", "to", "recipient")
        body = self._extract_body(payload)
        if not sender or not recipient or not body:
            event = EmailWebhookEvent(
                provider=self.provider_name,
                event_type=self._extract_event_type(payload) or "reply",
                status="malformed",
                message_id=self._extract_message_id(payload),
                error_message="Inbound email webhook payload is missing sender, recipient, or body.",
            )
            raise MalformedWebhookPayloadError(event.error_message, event)
        return InboundMessage(
            channel=Channel.EMAIL,
            sender=sender,
            recipient=recipient,
            body=body,
        )

    def _extract_string(self, payload: dict, *keys: str) -> str:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = payload.get("data")
        if isinstance(data, dict):
            for key in keys:
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return ""

    def _extract_body(self, payload: dict) -> str:
        for key in ("text", "body", "reply_text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("text", "body", "reply_text"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            reply = data.get("reply")
            if isinstance(reply, dict):
                for key in ("text", "body"):
                    value = reply.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
        return ""
