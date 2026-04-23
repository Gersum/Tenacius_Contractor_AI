from __future__ import annotations

from pathlib import Path
from typing import Callable

from agent.models.schemas import Channel, InboundMessage, LeadRecord, SmsDeliveryResult, SmsWebhookEvent
from agent.utils.serialization import write_json


class SmsHandlerError(RuntimeError):
    """Base exception for SMS handler failures."""


class SmsDeliveryError(SmsHandlerError):
    """Raised when an outbound SMS cannot be completed safely."""

    def __init__(self, message: str, result: SmsDeliveryResult) -> None:
        super().__init__(message)
        self.result = result


class MalformedWebhookPayloadError(SmsHandlerError):
    """Raised when a provider webhook payload is malformed."""

    def __init__(self, message: str, event: SmsWebhookEvent) -> None:
        super().__init__(message)
        self.event = event


InboundSmsHandler = Callable[[InboundMessage], None]


class SmsHandler:
    """Africa's Talking-style sink adapter with inbound webhook handling."""

    def __init__(
        self,
        runtime_dir: Path,
        provider_name: str,
        sink_mode: bool,
        inbound_handler: InboundSmsHandler | None = None,
    ) -> None:
        self.runtime_dir = runtime_dir / "sms"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.provider_name = provider_name
        self.sink_mode = sink_mode
        self.inbound_handler = inbound_handler

    def register_inbound_handler(self, handler: InboundSmsHandler) -> None:
        self.inbound_handler = handler

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

        validation_error = self._validate_outbound(lead, message)
        if validation_error is not None:
            result.status = "failed"
            write_json(Path(result.preview_ref), result)
            raise SmsDeliveryError(validation_error, result)

        write_json(Path(result.preview_ref), result)
        return result

    def handle_webhook(self, payload: dict, provider_name: str | None = None) -> SmsWebhookEvent:
        provider = provider_name or self.provider_name
        event_type = self._extract_event_type(payload)
        message_id = self._extract_message_id(payload)
        payload_ref = str(self.runtime_dir / f"webhook_{message_id or 'unknown'}.json")

        if event_type is None:
            event = SmsWebhookEvent(
                provider=provider,
                event_type="unknown",
                status="malformed",
                message_id=message_id,
                payload_ref=payload_ref,
                error_message="Missing provider event type in SMS webhook payload.",
            )
            write_json(Path(payload_ref), {"payload": payload, "event": event})
            raise MalformedWebhookPayloadError(event.error_message, event)

        if event_type in {"sms.received", "inbound.sms", "reply", "sms.reply"}:
            inbound = self._build_inbound_message(payload)
            event = SmsWebhookEvent(
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

        if event_type in {"sms.delivered", "delivered", "delivery.receipt"}:
            event = SmsWebhookEvent(
                provider=provider,
                event_type=event_type,
                status="delivered",
                message_id=message_id,
                payload_ref=payload_ref,
            )
            write_json(Path(payload_ref), {"payload": payload, "event": event})
            return event

        event = SmsWebhookEvent(
            provider=provider,
            event_type=event_type,
            status="ignored",
            message_id=message_id,
            payload_ref=payload_ref,
            error_message=f"Unhandled SMS webhook event type: {event_type}",
        )
        write_json(Path(payload_ref), {"payload": payload, "event": event})
        return event

    def _validate_outbound(self, lead: LeadRecord, message: str) -> str | None:
        if not lead.synthetic_contact_phone or not lead.synthetic_contact_phone.strip():
            return "Outbound SMS send failed: recipient phone number is required."
        if not message.strip():
            return "Outbound SMS send failed: body is required."
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
        for key in ("message_id", "sms_id", "id"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("message_id", "sms_id", "id"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def _build_inbound_message(self, payload: dict) -> InboundMessage:
        sender = self._extract_string(payload, "from_number", "from", "sender")
        recipient = self._extract_string(payload, "to_number", "to", "recipient")
        body = self._extract_string(payload, "text", "body", "message")
        if not sender or not recipient or not body:
            event = SmsWebhookEvent(
                provider=self.provider_name,
                event_type=self._extract_event_type(payload) or "reply",
                status="malformed",
                message_id=self._extract_message_id(payload),
                error_message="Inbound SMS webhook payload is missing sender, recipient, or body.",
            )
            raise MalformedWebhookPayloadError(event.error_message, event)
        return InboundMessage(
            channel=Channel.SMS,
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
