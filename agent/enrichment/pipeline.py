from __future__ import annotations

from agent.config import Settings
from agent.enrichment.layoffs import LayoffsLookup
from agent.enrichment.public_signals import PublicSignalCollector
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

    def build_hiring_signal_brief(self, lead: LeadRecord) -> HiringSignalBrief:
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
        return CompetitorGapBrief(
            company_name=lead.company_name,
            sector="B2B software",
            peer_group_definition="Series A/B B2B software companies showing hiring or delivery-scale pressure",
            prospect_position_summary=(
                "Relative to a fast-growing peer set, the prospect shows early growth signals but not a strongly visible delivery-capacity story."
            ),
            recommended_hook=(
                "Lead with a grounded note about growth pressure and ask whether delivery bandwidth is keeping pace with hiring plans."
            ),
            confidence=hiring_signal_brief.segment_confidence,
            top_quartile_companies=["Peer Alpha", "Peer Beta", "Peer Gamma"],
            gap_findings=[
                GapFinding(
                    title="Delivery-capacity visibility gap",
                    description="Peer companies present clearer evidence of structured engineering scale than the prospect currently does.",
                    confidence=ConfidenceLevel.MEDIUM,
                )
            ],
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
