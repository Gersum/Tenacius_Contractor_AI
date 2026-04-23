from __future__ import annotations

from pathlib import Path

from agent.models.schemas import CalendarBooking, LeadRecord
from agent.utils.serialization import write_json


class CalComBookingClient:
    """Local Cal.com booking stub that persists a confirmed synthetic booking."""

    def __init__(self, runtime_dir: Path, event_type_slug: str) -> None:
        self.runtime_dir = runtime_dir / "calcom"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.event_type_slug = event_type_slug or "discovery-call"

    def book_discovery_call(self, lead: LeadRecord, sdr_email: str) -> CalendarBooking:
        booking = CalendarBooking(
            booking_id=f"booking_{lead.lead_id}",
            event_type_slug=self.event_type_slug,
            attendee_email=lead.synthetic_contact_email,
            host_email=sdr_email,
            scheduled_for="2026-04-24T14:00:00+03:00",
            booking_url=f"https://cal.example/{self.event_type_slug}/{lead.lead_id}",
            preview_ref=str(self.runtime_dir / f"{lead.lead_id}.json"),
        )
        write_json(Path(booking.preview_ref), booking)
        return booking
