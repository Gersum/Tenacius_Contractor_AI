from __future__ import annotations

from agent.models.schemas import InboundMessage


def should_switch_to_sms(message: InboundMessage) -> bool:
    text = message.body.lower()
    return any(keyword in text for keyword in ("text me", "sms", "text ", "phone"))
