from __future__ import annotations

import json

from agent.config import Settings
from agent.llm.openrouter import OpenRouterClient, OpenRouterError
from agent.materials.tenacious import EmailPromptMaterial, TenaciousSalesMaterials
from agent.models.schemas import (
    Channel,
    CompetitorGapBrief,
    ConfidenceLevel,
    ICPSegment,
    HiringSignalBrief,
    LeadRecord,
    MessageDraft,
)
from agent.policies.bench_commitment import bench_safe_value_prop


class GroundingPolicy:
    """Turns enrichment signals into confidence-aware outreach."""

    TEMPLATE_PROMPT_VERSION = "grounded_email_template_v1"
    OPENROUTER_PROMPT_VERSION = "grounded_email_openrouter_v1"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.materials = TenaciousSalesMaterials(settings.project_root)
        self.openrouter_client = (
            OpenRouterClient(
                api_key=settings.openrouter_api_key,
                app_name=settings.app_name,
                base_url=settings.openrouter_base_url,
                model=settings.openrouter_model,
            )
            if settings.openrouter_api_key
            else None
        )

    def compose_email(
        self,
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
    ) -> MessageDraft:
        prompt_materials = self.materials.prompt_materials(lead, hiring_signal_brief, competitor_gap_brief)
        fallback_draft = self._compose_template_email(
            lead=lead,
            hiring_signal_brief=hiring_signal_brief,
            competitor_gap_brief=competitor_gap_brief,
            prompt_materials=prompt_materials,
        )
        if self.openrouter_client is None:
            return fallback_draft

        try:
            generation = self.openrouter_client.create_chat_completion(
                messages=[
                    {"role": "system", "content": self._system_prompt(prompt_materials)},
                    {
                        "role": "user",
                        "content": self._user_prompt(
                            lead=lead,
                            hiring_signal_brief=hiring_signal_brief,
                            competitor_gap_brief=competitor_gap_brief,
                            prompt_materials=prompt_materials,
                        ),
                    },
                ],
                temperature=0.25,
                max_completion_tokens=350,
                response_format={"type": "json_object"},
                metadata={
                    "workflow": "compose_initial_outreach",
                    "lead_id": lead.lead_id,
                    "channel": "email",
                },
            )
            payload = self._parse_model_payload(generation.content)
            return MessageDraft(
                channel=Channel.EMAIL,
                body=self._coerce_string(payload.get("body"), fallback_draft.body),
                subject=self._coerce_string(payload.get("subject"), fallback_draft.subject),
                variant_tag=self.OPENROUTER_PROMPT_VERSION,
                prompt_version=self.OPENROUTER_PROMPT_VERSION,
                confidence=hiring_signal_brief.segment_confidence,
                source_backed_claims=self._coerce_claims(
                    payload.get("source_backed_claims"),
                    fallback_draft.source_backed_claims,
                ),
                generation_provider="openrouter",
                generation_model=generation.model or self.settings.openrouter_model or None,
                generation_mode="openrouter",
                generation_cost_usd=generation.cost_usd,
            )
        except OpenRouterError as exc:
            return MessageDraft(
                channel=fallback_draft.channel,
                body=fallback_draft.body,
                subject=fallback_draft.subject,
                variant_tag="grounded_email_openrouter_fallback_v1",
                prompt_version=self.OPENROUTER_PROMPT_VERSION,
                confidence=fallback_draft.confidence,
                source_backed_claims=fallback_draft.source_backed_claims,
                generation_provider="openrouter",
                generation_model=self.settings.openrouter_model or None,
                generation_mode="fallback_template",
                generation_cost_usd=0.0,
                generation_error=str(exc),
            )

    def _compose_template_email(
        self,
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
        prompt_materials: EmailPromptMaterial,
    ) -> MessageDraft:
        opening = {
            ConfidenceLevel.HIGH: "The public signals are strong enough to say",
            ConfidenceLevel.MEDIUM: "From the public signals we could verify, it looks like",
            ConfidenceLevel.LOW: "I may be missing context, but the public signals suggest",
        }[hiring_signal_brief.segment_confidence]
        pitch_line = self._segment_pitch_line(hiring_signal_brief)
        gap_line = self._prospect_safe_gap_line(competitor_gap_brief)
        materials_note = "The attached case studies back the pattern if you want a reference point."

        body = (
            f"Hi {lead.synthetic_contact_name},\n\n"
            f"{opening} {lead.company_name} may be entering a period where delivery demand rises faster than hiring can absorb. "
            f"We saw {hiring_signal_brief.funding_signal.value}, and the public hiring picture suggests there may be some growth pressure.\n\n"
            f"For teams at that stage, Tenacious can help {pitch_line} {gap_line}\n\n"
            f"{bench_safe_value_prop()} {materials_note}\n\n"
            "If that is directionally true, I can share a short point of view or line up a 30-minute discovery call.\n"
        )
        return MessageDraft(
            channel=Channel.EMAIL,
            body=body,
            subject=f"{lead.company_name} delivery capacity and hiring pressure",
            variant_tag=self.TEMPLATE_PROMPT_VERSION,
            prompt_version=self.TEMPLATE_PROMPT_VERSION,
            confidence=hiring_signal_brief.segment_confidence,
            source_backed_claims=[
                hiring_signal_brief.funding_signal.value,
                hiring_signal_brief.job_post_signal.value,
                competitor_gap_brief.prospect_position_summary,
            ],
            generation_provider="local_template",
            generation_model=None,
            generation_mode="template",
        )

    def _segment_pitch_line(self, hiring_signal_brief: HiringSignalBrief) -> str:
        if hiring_signal_brief.segment_recommendation == ICPSegment.RECENTLY_FUNDED:
            if hiring_signal_brief.ai_maturity_score >= 2:
                return "scale your AI team faster than in-house hiring can support."
            return "stand up your first AI function with a dedicated squad."
        if hiring_signal_brief.segment_recommendation == ICPSegment.COST_RESTRUCTURING:
            if hiring_signal_brief.ai_maturity_score >= 2:
                return "preserve your AI delivery capacity while reshaping cost structure."
            return "maintain platform delivery velocity through the restructure."
        if hiring_signal_brief.segment_recommendation == ICPSegment.LEADERSHIP_TRANSITION:
            return "the first 90 days are when vendor mix gets reassessed."
        if hiring_signal_brief.segment_recommendation == ICPSegment.CAPABILITY_GAP:
            return "the question is whether the capability gap is already being built in-house or still needs support."
        return "the public signals suggest a concrete delivery question worth testing."

    def _prospect_safe_gap_line(self, competitor_gap_brief: CompetitorGapBrief) -> str:
        high_confidence_gaps = [
            gap for gap in competitor_gap_brief.gap_findings if gap.confidence == ConfidenceLevel.HIGH
        ]
        if high_confidence_gaps:
            title = high_confidence_gaps[0].title.rstrip(".")
            return (
                "One research question worth validating is whether "
                f"{title.lower()} is a current priority or intentionally out of scope."
            )
        return (
            "The competitor-gap brief also suggests a few questions worth validating, "
            "but I would treat them as hypotheses rather than claims."
        )

    def _system_prompt(self, prompt_materials: EmailPromptMaterial) -> str:
        return (
            "You write outbound sales emails for Tenacious Consulting and Outsourcing. "
            "Use only the provided public signals. Do not invent facts, logos, case studies, or certainty. "
            "Email is the primary channel. Do not mention SMS or voice in the first outreach. "
            "Keep the email concise, plain text, and grounded. Return only JSON. "
            "Follow the attached style guide and pricing guardrails. "
            f"Style markers: {prompt_materials.style_guide[:240]}"
        )

    def _user_prompt(
        self,
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
        prompt_materials: EmailPromptMaterial,
    ) -> str:
        context = {
            "lead": {
                "company_name": lead.company_name,
                "contact_name": lead.synthetic_contact_name,
                "contact_email": lead.synthetic_contact_email,
            },
            "signals": {
                "segment_confidence": hiring_signal_brief.segment_confidence.value,
                "funding_signal": hiring_signal_brief.funding_signal.value,
                "job_post_signal": hiring_signal_brief.job_post_signal.value,
                "layoff_signal": hiring_signal_brief.layoff_signal.value,
                "leadership_change_signal": hiring_signal_brief.leadership_change_signal.value,
                "ai_maturity_score": hiring_signal_brief.ai_maturity_score,
                "ai_maturity_reasoning": hiring_signal_brief.ai_maturity_reasoning,
                "bench_match_summary": hiring_signal_brief.bench_match_summary,
            },
            "competitor_gap": {
                "prospect_position_summary": competitor_gap_brief.prospect_position_summary,
                "recommended_hook": competitor_gap_brief.recommended_hook,
            },
            "safe_value_prop": bench_safe_value_prop(),
            "tenacious_materials": {
                "icp_definition": prompt_materials.icp_definition[:2200],
                "pricing_guardrails": prompt_materials.pricing_sheet[:1800],
                "cold_sequence": prompt_materials.cold_sequence[:2500],
                "warm_sequence": prompt_materials.warm_sequence[:2200],
                "reengagement_sequence": prompt_materials.reengagement_sequence[:1800],
                "case_studies": prompt_materials.case_studies[:1800],
                "bench_summary": prompt_materials.bench_summary,
                "baseline_numbers": prompt_materials.baseline_numbers[:1400],
            },
        }
        return (
            "Draft a single cold outbound email for the lead below.\n"
            "Requirements:\n"
            "- plain text body under 170 words\n"
            "- use softer language when confidence is medium or low\n"
            "- mention only facts that appear in the context\n"
            "- ask for a short 30-minute discovery call\n"
            "- no bullet points, no markdown\n"
            '- return strict JSON with keys "subject", "body", and "source_backed_claims"\n\n'
            f"Context:\n{json.dumps(context, indent=2)}"
        )

    def _parse_model_payload(self, content: str) -> dict:
        stripped = content.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise OpenRouterError("OpenRouter draft could not be parsed as JSON.")
            try:
                return json.loads(stripped[start : end + 1])
            except json.JSONDecodeError as exc:
                raise OpenRouterError("OpenRouter draft JSON was malformed.") from exc

    def _coerce_string(self, value: object, fallback: str | None) -> str:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                return cleaned
        return fallback or ""

    def _coerce_claims(self, value: object, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if cleaned:
                return cleaned
        return fallback
