from __future__ import annotations

from agent.config import Settings
from agent.enrichment.layoffs import LayoffsLookup
from agent.enrichment.public_signals import PublicSignalCollector
from agent.materials.tenacious import TenaciousSalesMaterials
from agent.models.schemas import (
    CompetitorGapBrief,
    ConfidenceLevel,
    GapFinding,
    HiringSignalBrief,
    ICPSegment,
    LeadRecord,
    ScoredSignal,
)


def _slugify(value: str) -> str:
    return value.lower().replace(" ", "-")


class EnrichmentPipeline:
    """Public-signal enrichment pipeline shaped around public, compliance-safe collection."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.layoffs_lookup = LayoffsLookup(settings.layoffs_csv_path)
        self.materials = TenaciousSalesMaterials(settings.project_root)

    def build_hiring_signal_brief(self, lead: LeadRecord) -> HiringSignalBrief:
        if self.settings.use_seeded_demo_data and self.materials.has_seed_for(lead):
            layoff_signal = self.layoffs_lookup.build_signal(lead.company_name)
            return self.materials.build_seed_hiring_signal_brief(lead, layoff_signal=layoff_signal)

        public_signals = PublicSignalCollector(company_name=lead.company_name, domain=lead.domain)
        funding_signal, job_post_signal, leadership_change_signal = public_signals.collect_all()
        layoff_signal = self.layoffs_lookup.build_signal(lead.company_name)
        source_refs = [
            *funding_signal.source_refs,
            *job_post_signal.source_refs,
            *leadership_change_signal.source_refs,
            *layoff_signal.source_refs,
        ]
        return HiringSignalBrief(
            company_name=lead.company_name,
            crunchbase_ref=f"https://www.crunchbase.com/organization/{_slugify(lead.company_name)}",
            segment_recommendation=self._infer_segment_recommendation(
                funding_signal=funding_signal,
                job_post_signal=job_post_signal,
                leadership_change_signal=leadership_change_signal,
                layoff_signal=layoff_signal,
            ),
            segment_confidence=self._infer_segment_confidence(
                funding_signal=funding_signal,
                job_post_signal=job_post_signal,
                leadership_change_signal=leadership_change_signal,
                layoff_signal=layoff_signal,
            ),
            funding_signal=funding_signal,
            job_post_signal=job_post_signal,
            layoff_signal=layoff_signal,
            leadership_change_signal=leadership_change_signal,
            ai_maturity_score=self._infer_ai_maturity_score(
                funding_signal=funding_signal,
                job_post_signal=job_post_signal,
                leadership_change_signal=leadership_change_signal,
                layoff_signal=layoff_signal,
            ),
            ai_maturity_reasoning=[
                f"Crunchbase funding confidence: {funding_signal.confidence.value}.",
                f"Public job-post confidence: {job_post_signal.confidence.value}.",
                f"Leadership-change confidence: {leadership_change_signal.confidence.value}.",
                f"Layoff confidence: {layoff_signal.confidence.value}.",
            ],
            bench_match_summary=self._build_bench_match_summary(
                funding_signal=funding_signal,
                job_post_signal=job_post_signal,
                leadership_change_signal=leadership_change_signal,
                layoff_signal=layoff_signal,
            ),
            source_refs=source_refs,
        )

    def build_competitor_gap_brief(
        self, lead: LeadRecord, hiring_signal_brief: HiringSignalBrief
    ) -> CompetitorGapBrief:
        if self.settings.use_seeded_demo_data and self.materials.has_seed_for(lead):
            return self.materials.build_seed_competitor_gap_brief(lead)
        return self._build_live_competitor_gap_brief(lead, hiring_signal_brief)

    def _build_live_competitor_gap_brief(
        self,
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
    ) -> CompetitorGapBrief:
        gap_findings = [
            GapFinding(
                title="Hiring velocity compared with delivery capacity",
                description=(
                    f"{lead.company_name}'s current public hiring signal is: "
                    f"{hiring_signal_brief.job_post_signal.value}"
                ),
                confidence=hiring_signal_brief.job_post_signal.confidence,
            ),
            GapFinding(
                title="Leadership or operating-change signal",
                description=(
                    f"{lead.company_name}'s public leadership signal is: "
                    f"{hiring_signal_brief.leadership_change_signal.value}"
                ),
                confidence=hiring_signal_brief.leadership_change_signal.confidence,
            ),
            GapFinding(
                title="Funding, layoff, and AI maturity pressure",
                description=(
                    f"Funding confidence is {hiring_signal_brief.funding_signal.confidence.value}; "
                    f"layoff confidence is {hiring_signal_brief.layoff_signal.confidence.value}; "
                    f"AI maturity score is {hiring_signal_brief.ai_maturity_score}/3."
                ),
                confidence=hiring_signal_brief.segment_confidence,
            ),
        ]
        strongest = max(
            gap_findings,
            key=lambda finding: {"low": 1, "medium": 2, "high": 3}[finding.confidence.value],
        )
        return CompetitorGapBrief(
            company_name=lead.company_name,
            sector="Live public-web classification",
            peer_group_definition=(
                "Live mode uses the prospect's public funding, careers, layoffs, and leadership signals. "
                "No attached sample competitor names are injected unless USE_SEEDED_DEMO_DATA=true."
            ),
            prospect_position_summary=(
                f"{lead.company_name} is classified as {hiring_signal_brief.segment_recommendation.value} "
                f"with {hiring_signal_brief.segment_confidence.value} confidence from live public evidence."
            ),
            recommended_hook=strongest.description,
            confidence=hiring_signal_brief.segment_confidence,
            top_quartile_companies=[],
            gap_findings=gap_findings,
            source_refs=hiring_signal_brief.source_refs,
        )

    def _infer_segment_recommendation(
        self,
        funding_signal: ScoredSignal,
        job_post_signal: ScoredSignal,
        leadership_change_signal: ScoredSignal,
        layoff_signal: ScoredSignal,
    ) -> ICPSegment:
        if layoff_signal.confidence == ConfidenceLevel.HIGH and job_post_signal.confidence == ConfidenceLevel.LOW:
            return ICPSegment.COST_RESTRUCTURING
        if leadership_change_signal.confidence == ConfidenceLevel.HIGH and job_post_signal.confidence != ConfidenceLevel.LOW:
            return ICPSegment.LEADERSHIP_TRANSITION
        if funding_signal.confidence != ConfidenceLevel.LOW or job_post_signal.confidence != ConfidenceLevel.LOW:
            return ICPSegment.RECENTLY_FUNDED
        return ICPSegment.UNKNOWN

    def _infer_segment_confidence(
        self,
        funding_signal: ScoredSignal,
        job_post_signal: ScoredSignal,
        leadership_change_signal: ScoredSignal,
        layoff_signal: ScoredSignal,
    ) -> ConfidenceLevel:
        signals = [funding_signal, job_post_signal, leadership_change_signal, layoff_signal]
        if any(signal.confidence == ConfidenceLevel.HIGH for signal in signals):
            return ConfidenceLevel.HIGH
        if any(signal.confidence == ConfidenceLevel.MEDIUM for signal in signals):
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _infer_ai_maturity_score(
        self,
        funding_signal: ScoredSignal,
        job_post_signal: ScoredSignal,
        leadership_change_signal: ScoredSignal,
        layoff_signal: ScoredSignal,
    ) -> int:
        score = 0
        for signal in (funding_signal, job_post_signal, leadership_change_signal):
            if signal.confidence in {ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM}:
                score += 1
        if layoff_signal.confidence == ConfidenceLevel.HIGH:
            score += 1
        return min(score, 3)

    def _build_bench_match_summary(
        self,
        funding_signal: ScoredSignal,
        job_post_signal: ScoredSignal,
        leadership_change_signal: ScoredSignal,
        layoff_signal: ScoredSignal,
    ) -> str:
        active_signals = [
            signal.name
            for signal in (funding_signal, job_post_signal, leadership_change_signal, layoff_signal)
            if signal.confidence in {ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM}
        ]
        if not active_signals:
            return "Bench match remains exploratory until public signals are available."
        joined = ", ".join(active_signals)
        return f"Bench match is guided by public signals from {joined}."
