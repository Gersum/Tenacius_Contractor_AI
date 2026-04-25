from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable
from urllib import error, request
from datetime import UTC, datetime, timedelta

from agent.models.schemas import CalendarBooking, CalendarWebhookEvent, LeadRecord
from agent.utils.serialization import write_json


class CalComBookingError(RuntimeError):
    """Raised when a real Cal.com booking attempt fails and fallback is disabled."""

    def __init__(self, message: str, booking: CalendarBooking) -> None:
        super().__init__(message)
        self.booking = booking


class InvalidCalComWebhookError(ValueError):
    """Raised when an inbound Cal.com webhook payload cannot be parsed safely."""


class CalComBookingClient:
    """Self-hosted Cal.com client with a clear local fallback for demos."""

    def __init__(
        self,
        runtime_dir: Path,
        base_url: str,
        api_key: str,
        event_type_slug: str,
        api_version: str,
        host_username: str,
        default_start: str,
        app_base_url: str | None = None,
        api_base_url: str | None = None,
        event_type_id: int | None = None,
        fallback_enabled: bool = True,
        webhook_secret: str = "",
        inbound_handler: Callable[[CalendarWebhookEvent], None] | None = None,
    ) -> None:
        self.runtime_dir = runtime_dir / "calcom"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = (base_url or "http://127.0.0.1:3001").rstrip("/")
        self.app_base_url = (app_base_url or self.base_url).rstrip("/")
        self.api_base_url = (api_base_url or self.base_url).rstrip("/")
        self.api_key = api_key.strip()
        self.event_type_slug = event_type_slug or "discovery-call"
        self.event_type_id = event_type_id
        self.api_version = api_version or "2026-02-25"
        self.host_username = host_username.strip()
        self.default_start = default_start or "2026-04-24T11:00:00Z"
        self.fallback_enabled = fallback_enabled
        self.webhook_secret = webhook_secret.strip()
        self.inbound_handler = inbound_handler
        self.booking_endpoint_candidates = self._build_booking_endpoint_candidates()

    def book_discovery_call(self, lead: LeadRecord, sdr_email: str) -> CalendarBooking:
        if self.api_key:
            try:
                return self._book_via_api(lead, sdr_email)
            except Exception as exc:  # pragma: no cover - exercised through tests with deterministic patching
                if not self.fallback_enabled:
                    failed = self._build_booking(
                        lead=lead,
                        sdr_email=sdr_email,
                        booking_id=f"booking_failed_{lead.lead_id}",
                        scheduled_for=self.default_start,
                        booking_url=f"{self.app_base_url}/bookings/{lead.lead_id}",
                        mode="error",
                        status="failed",
                        error_message=str(exc),
                    )
                    self._persist_booking(failed, extra={"failure_mode": "live_request_failed"})
                    raise CalComBookingError(str(exc), failed) from exc
                return self._book_via_fallback(lead, sdr_email, str(exc))
        return self._book_via_fallback(lead, sdr_email, "CALCOM_API_KEY not configured")

    def handle_webhook(
        self,
        payload: dict[str, Any],
        signature: str | None = None,
    ) -> CalendarWebhookEvent:
        event_id = str(
            payload.get("id")
            or payload.get("bookingId")
            or payload.get("bookingUid")
            or payload.get("uid")
            or "unknown"
        )
        payload_ref = self.runtime_dir / f"webhook_{event_id}.json"
        write_json(payload_ref, payload)

        if self.webhook_secret and signature != self.webhook_secret:
            event = CalendarWebhookEvent(
                provider="cal.com",
                event_type=str(payload.get("triggerEvent") or payload.get("type") or "unknown"),
                status="rejected",
                booking_id=event_id,
                payload_ref=str(payload_ref),
                error_message="Invalid webhook secret",
            )
            write_json(self.runtime_dir / f"webhook_event_{event_id}.json", event)
            raise InvalidCalComWebhookError("Invalid webhook secret")

        event_type = str(payload.get("triggerEvent") or payload.get("type") or "").strip()
        if not event_type:
            event = CalendarWebhookEvent(
                provider="cal.com",
                event_type="unknown",
                status="invalid",
                booking_id=event_id,
                payload_ref=str(payload_ref),
                error_message="Missing event type",
            )
            write_json(self.runtime_dir / f"webhook_event_{event_id}.json", event)
            raise InvalidCalComWebhookError("Missing Cal.com webhook event type")

        normalized = event_type.lower()
        if "cancel" in normalized:
            status = "cancelled"
        elif "create" in normalized:
            status = "booked"
        elif "resched" in normalized:
            status = "rescheduled"
        else:
            status = "received"

        event = CalendarWebhookEvent(
            provider="cal.com",
            event_type=event_type,
            status=status,
            booking_id=event_id,
            payload_ref=str(payload_ref),
        )
        write_json(self.runtime_dir / f"webhook_event_{event_id}.json", event)
        if self.inbound_handler is not None:
            self.inbound_handler(event)
        return event

    def _book_via_api(self, lead: LeadRecord, sdr_email: str) -> CalendarBooking:
        payload = {
            "start": self._resolve_booking_start(),
            "eventTypeSlug": self.event_type_slug,
            "attendee": {
                "name": lead.synthetic_contact_name,
                "email": lead.synthetic_contact_email,
                "timeZone": "Africa/Addis_Ababa",
                "phoneNumber": lead.synthetic_contact_phone or "",
                "language": "en",
            },
            "metadata": {
                "leadId": lead.lead_id,
                "companyName": lead.company_name,
                "domain": lead.domain,
                "sourceType": lead.source_type,
            },
            "lengthInMinutes": 30,
        }
        if self.host_username:
            payload["username"] = self.host_username

        try:
            raw_response = self._post_booking(payload)
        except RuntimeError as exc:
            if self.event_type_id is None:
                raise
            raw_response = self._post_legacy_booking(payload, lead)
        data = raw_response.get("data", raw_response) if isinstance(raw_response, dict) else {}
        booking_uid = str(data.get("uid") or data.get("id") or f"booking_{lead.lead_id}")
        booking_url = self._extract_booking_url(data, booking_uid)
        scheduled_for = str(data.get("start") or data.get("startTime") or self.default_start)

        booking = self._build_booking(
            lead=lead,
            sdr_email=sdr_email,
            booking_id=booking_uid,
            scheduled_for=scheduled_for,
            booking_url=booking_url,
            mode="api",
            status="confirmed",
            raw_response_ref=str(self.runtime_dir / f"{lead.lead_id}_raw.json"),
        )
        self._persist_booking(booking, extra={"request": payload, "response": raw_response})
        return booking

    def _book_via_fallback(self, lead: LeadRecord, sdr_email: str, reason: str) -> CalendarBooking:
        booking = self._build_booking(
            lead=lead,
            sdr_email=sdr_email,
            booking_id=f"booking_{lead.lead_id}",
            scheduled_for=self.default_start,
            booking_url=f"{self.app_base_url}/bookings/{self.event_type_slug}?lead={lead.lead_id}",
            mode="fallback",
            status="simulated",
            error_message=reason,
        )
        self._persist_booking(booking, extra={"fallback_reason": reason})
        return booking

    def _build_booking(
        self,
        lead: LeadRecord,
        sdr_email: str,
        booking_id: str,
        scheduled_for: str,
        booking_url: str,
        mode: str,
        status: str,
        raw_response_ref: str | None = None,
        error_message: str | None = None,
    ) -> CalendarBooking:
        return CalendarBooking(
            booking_id=booking_id,
            event_type_slug=self.event_type_slug,
            attendee_email=lead.synthetic_contact_email,
            host_email=sdr_email,
            scheduled_for=scheduled_for,
            booking_url=booking_url,
            preview_ref=str(self.runtime_dir / f"{lead.lead_id}.json"),
            provider="cal.com",
            mode=mode,
            status=status,
            host_username=self.host_username or None,
            raw_response_ref=raw_response_ref,
            error_message=error_message,
        )

    def _persist_booking(self, booking: CalendarBooking, extra: dict[str, Any] | None = None) -> None:
        raw_path = Path(booking.raw_response_ref) if booking.raw_response_ref else None
        if raw_path is not None and extra is not None:
            write_json(raw_path, extra)
        payload = {
            "booking": booking,
            "metadata": extra or {},
        }
        write_json(Path(booking.preview_ref), payload)

    def _post_booking(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: RuntimeError | None = None
        saw_not_found = False
        saw_unreachable = False
        ended_on_unreachable = False
        for endpoint in self.booking_endpoint_candidates:
            try:
                return self._post_booking_to_endpoint(endpoint, payload)
            except RuntimeError as exc:
                message = str(exc)
                if "HTTP 404" in message:
                    saw_not_found = True
                    last_error = exc
                    ended_on_unreachable = False
                    continue
                if "failed: " in message:
                    saw_unreachable = True
                    last_error = exc
                    ended_on_unreachable = True
                    continue
                last_error = exc
                ended_on_unreachable = False
                break

        if saw_unreachable and ended_on_unreachable and last_error is not None:
            raise RuntimeError(
                "Cal.com API server was unreachable on the configured booking endpoints. Check that the "
                "self-hosted API is running on one of: "
                f"{', '.join(self.booking_endpoint_candidates)}."
            ) from last_error

        if saw_not_found and last_error is not None:
            attempted = ", ".join(self.booking_endpoint_candidates)
            raise RuntimeError(
                "Cal.com booking endpoint was not found on the configured API server. "
                f"Tried: {attempted}. Last error: {last_error}"
            ) from last_error

        if last_error is not None:
            raise last_error
        raise RuntimeError("Cal.com booking request failed before any endpoint could be attempted.")

    def _post_booking_to_endpoint(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "cal-api-version": self.api_version,
        }
        req = request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=15) as response:
                response_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Cal.com booking request failed with HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Cal.com booking request failed: {exc.reason}") from exc

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Cal.com booking response was not valid JSON") from exc

    def _build_booking_endpoint_candidates(self) -> list[str]:
        bases = [self.api_base_url.rstrip("/")]
        app_base = self.app_base_url.rstrip("/")
        if app_base not in bases:
            bases.append(app_base)

        candidates: list[str] = []
        for base in bases:
            candidates.extend(
                [
                    f"{base}/v2/bookings",
                    f"{base}/api/v2/bookings",
                ]
            )
        deduped: list[str] = []
        for candidate in candidates:
            if candidate not in deduped:
                deduped.append(candidate)
        return deduped

    def _extract_booking_url(self, data: dict[str, Any], booking_uid: str) -> str:
        direct = data.get("bookingUrl") or data.get("rescheduleUrl")
        if isinstance(direct, str) and direct.strip():
            return direct

        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            meta_url = metadata.get("bookingUrl")
            if isinstance(meta_url, str) and meta_url.strip():
                return meta_url

        return f"{self.app_base_url}/booking/{booking_uid}"

    def _post_legacy_booking(self, payload: dict[str, Any], lead: LeadRecord) -> dict[str, Any]:
        if self.event_type_id is None:
            raise RuntimeError("Cal.com legacy booking fallback requires CALCOM_EVENT_TYPE_ID.")

        endpoint = f"{self.app_base_url.rstrip('/')}/api/book/event"
        start = str(payload["start"])
        last_error: RuntimeError | None = None
        for candidate_start in self._legacy_booking_start_candidates(start):
            legacy_payload = {
                "eventTypeId": self.event_type_id,
                "start": candidate_start,
                "end": self._calculate_end_time(candidate_start, int(payload.get("lengthInMinutes", 30))),
                "timeZone": payload["attendee"]["timeZone"],
                "language": payload["attendee"]["language"],
                "metadata": payload["metadata"],
                "responses": {
                    "email": lead.synthetic_contact_email,
                    "name": lead.synthetic_contact_name,
                    "location": {
                        "optionValue": "",
                        "value": "integrations:daily",
                    },
                },
            }
            try:
                return self._post_booking_to_endpoint(endpoint, legacy_payload)
            except RuntimeError as exc:
                last_error = exc
                if "no_available_users_found_error" not in str(exc):
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Cal.com legacy booking fallback failed before any slot could be attempted.")

    def _resolve_booking_start(self) -> str:
        try:
            requested = datetime.fromisoformat(self.default_start.replace("Z", "+00:00"))
        except ValueError:
            return self.default_start

        now = datetime.now(UTC)
        if requested > now + timedelta(minutes=30):
            return requested.astimezone(UTC).isoformat().replace("+00:00", "Z")

        future = now + timedelta(days=3)
        future = future.replace(hour=11, minute=0, second=0, microsecond=0)
        return future.isoformat().replace("+00:00", "Z")

    def _calculate_end_time(self, start: str, length_minutes: int) -> str:
        parsed = datetime.fromisoformat(start.replace("Z", "+00:00"))
        return (parsed + timedelta(minutes=length_minutes)).isoformat().replace("+00:00", "Z")

    def _legacy_booking_start_candidates(self, start: str) -> list[str]:
        parsed = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(UTC)
        candidates: list[datetime] = [parsed]
        next_day = parsed + timedelta(days=1)
        business_hours = (9, 10, 11, 12)
        for day in (parsed, next_day):
            for hour in business_hours:
                candidate = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                if candidate not in candidates:
                    candidates.append(candidate)
        return [candidate.isoformat().replace("+00:00", "Z") for candidate in candidates]
