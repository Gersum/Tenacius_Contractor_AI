from __future__ import annotations

import json
import ssl
from pathlib import Path
from typing import Any
from urllib import error, request

from agent.models.schemas import (
    CalendarBooking,
    CompetitorGapBrief,
    ConversationState,
    HiringSignalBrief,
    HubSpotSyncResult,
    LeadRecord,
    QualificationDecision,
    utc_now,
)
from agent.utils.serialization import to_jsonable, write_json

try:
    import certifi
except ImportError:  # pragma: no cover - optional dependency fallback
    certifi = None


class HubSpotMCPClient:
    """Persist local CRM previews and upsert a real HubSpot contact when configured."""

    def __init__(self, runtime_dir: Path, access_token: str = "", portal_id: str = "") -> None:
        self.runtime_dir = runtime_dir / "hubspot"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.access_token = access_token.strip()
        self.portal_id = portal_id.strip()
        self.base_url = "https://api.hubapi.com"
        self.ssl_context = self._build_ssl_context()

    def sync_contact(
        self,
        lead: LeadRecord,
        conversation: ConversationState,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
        qualification: QualificationDecision,
        booking: CalendarBooking,
    ) -> HubSpotSyncResult:
        enriched_at = utc_now()
        preview_path = self.runtime_dir / f"{lead.lead_id}.json"
        all_properties = self._build_properties(
            lead=lead,
            conversation=conversation,
            hiring_signal_brief=hiring_signal_brief,
            competitor_gap_brief=competitor_gap_brief,
            qualification=qualification,
            booking=booking,
            enriched_at=enriched_at.isoformat(),
        )
        hubspot_properties = self._build_hubspot_properties(all_properties)

        preview_payload: dict[str, Any] = {
            "lead_id": lead.lead_id,
            "portal_id": self.portal_id or None,
            "mode": "stub" if not self.access_token else "live",
            "properties": all_properties,
            "hubspot_properties": hubspot_properties,
        }

        if not self.access_token:
            result = HubSpotSyncResult(
                record_id=f"hs_{lead.lead_id}",
                status="stubbed",
                preview_ref=str(preview_path),
                fields=all_properties,
            )
            preview_payload["result"] = to_jsonable(result)
            write_json(preview_path, preview_payload)
            return result

        try:
            contact_id, operation = self._upsert_contact(hubspot_properties)
            result = HubSpotSyncResult(
                record_id=contact_id,
                status=operation,
                preview_ref=str(preview_path),
                fields=all_properties,
            )
            preview_payload["result"] = to_jsonable(result)
            write_json(preview_path, preview_payload)
            return result
        except error.HTTPError as exc:
            error_message = self._format_http_error(exc)
            result = HubSpotSyncResult(
                record_id=f"hs_{lead.lead_id}",
                status="failed",
                preview_ref=str(preview_path),
                fields={**all_properties, "hubspot_error": error_message},
            )
            preview_payload["result"] = to_jsonable(result)
            preview_payload["error"] = error_message
            write_json(preview_path, preview_payload)
            return result
        except (error.URLError, ValueError, KeyError, json.JSONDecodeError) as exc:
            result = HubSpotSyncResult(
                record_id=f"hs_{lead.lead_id}",
                status="failed",
                preview_ref=str(preview_path),
                fields={**all_properties, "hubspot_error": str(exc)},
            )
            preview_payload["result"] = to_jsonable(result)
            preview_payload["error"] = str(exc)
            write_json(preview_path, preview_payload)
            return result

    def _build_properties(
        self,
        *,
        lead: LeadRecord,
        conversation: ConversationState,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
        qualification: QualificationDecision,
        booking: CalendarBooking,
        enriched_at: str,
    ) -> dict[str, Any]:
        return {
            "email": lead.synthetic_contact_email,
            "firstname": lead.synthetic_contact_name.split(" ", 1)[0] if lead.synthetic_contact_name else "",
            "lastname": lead.synthetic_contact_name.split(" ", 1)[1] if " " in lead.synthetic_contact_name else "",
            "company": lead.company_name,
            "phone": lead.synthetic_contact_phone,
            "website": lead.domain,
            "icp_segment": lead.icp_segment.value,
            "icp_confidence": lead.icp_confidence.value,
            "enrichment_timestamp": enriched_at,
            "conversation_stage": conversation.stage.value,
            "qualification_status": qualification.status,
            "booking_url": booking.booking_url,
            "ai_maturity_score": str(hiring_signal_brief.ai_maturity_score),
            "ai_maturity_reasoning": " | ".join(hiring_signal_brief.ai_maturity_reasoning),
            "funding_signal": hiring_signal_brief.funding_signal.value,
            "funding_confidence": hiring_signal_brief.funding_signal.confidence.value,
            "job_post_signal": hiring_signal_brief.job_post_signal.value,
            "job_post_confidence": hiring_signal_brief.job_post_signal.confidence.value,
            "layoff_signal": hiring_signal_brief.layoff_signal.value,
            "layoff_confidence": hiring_signal_brief.layoff_signal.confidence.value,
            "leadership_change_signal": hiring_signal_brief.leadership_change_signal.value,
            "leadership_change_confidence": hiring_signal_brief.leadership_change_signal.confidence.value,
            "bench_match_summary": hiring_signal_brief.bench_match_summary,
            "competitor_gap_position": competitor_gap_brief.prospect_position_summary,
            "recommended_hook": competitor_gap_brief.recommended_hook,
            "source_refs": json.dumps(
                to_jsonable(hiring_signal_brief.source_refs + competitor_gap_brief.source_refs),
                ensure_ascii=True,
            ),
        }

    def _upsert_contact(self, properties: dict[str, Any]) -> tuple[str, str]:
        existing_id = self._search_contact_id(properties["email"])
        if existing_id:
            body = {"properties": properties}
            response = self._hubspot_request(
                f"/crm/v3/objects/contacts/{existing_id}",
                method="PATCH",
                payload=body,
            )
            return str(response["id"]), "updated"

        body = {"properties": properties}
        response = self._hubspot_request(
            "/crm/v3/objects/contacts",
            method="POST",
            payload=body,
        )
        return str(response["id"]), "created"

    def _build_hubspot_properties(self, all_properties: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = ("email", "firstname", "lastname", "company", "phone", "website")
        return {key: value for key, value in all_properties.items() if key in allowed_keys and value}

    def _search_contact_id(self, email: str) -> str | None:
        body = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                }
            ],
            "properties": ["email"],
            "limit": 1,
        }
        response = self._hubspot_request(
            "/crm/v3/objects/contacts/search",
            method="POST",
            payload=body,
        )
        results = response.get("results", [])
        if not results:
            return None
        return str(results[0]["id"])

    def _hubspot_request(self, path: str, *, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=20, context=self.ssl_context) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("HubSpot API response was not a JSON object.")
        return parsed

    def _build_ssl_context(self) -> ssl.SSLContext:
        if certifi is not None:
            return ssl.create_default_context(cafile=certifi.where())
        return ssl.create_default_context()

    def _format_http_error(self, exc: error.HTTPError) -> str:
        body = ""
        if exc.fp is not None:
            try:
                body = exc.read().decode("utf-8", errors="replace").strip()
            except OSError:
                body = ""
        if body:
            return f"HTTP Error {exc.code}: {exc.reason} | {body}"
        return f"HTTP Error {exc.code}: {exc.reason}"
