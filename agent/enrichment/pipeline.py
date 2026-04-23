from __future__ import annotations

from agent.config import Settings
from agent.enrichment.layoffs import LayoffsLookup
from agent.models.schemas import (
    CompetitorGapBrief,
    ConfidenceLevel,
    GapFinding,
    HiringSignalBrief,
    ICPSegment,
    LeadRecord,
    ScoredSignal,
    SourceRef,
)


def _slugify(value: str) -> str:
    return value.lower().replace(" ", "-")


class EnrichmentPipeline:
    """Stub enrichment pipeline shaped like the real public-signal workflow."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.layoffs_lookup = LayoffsLookup(settings.layoffs_csv_path)

    def build_hiring_signal_brief(self, lead: LeadRecord) -> HiringSignalBrief:
        slug = _slugify(lead.company_name)
        source_refs = [
            SourceRef(
                title="Crunchbase sample placeholder",
                url=f"https://www.crunchbase.com/organization/{slug}",
                note="Replace with real Crunchbase ODM lookup.",
            ),
            SourceRef(
                title="BuiltIn jobs placeholder",
                url=f"https://www.builtin.com/company/{slug}/jobs",
                note="Replace with public job-post retrieval.",
            ),
        ]
        layoff_signal = self.layoffs_lookup.build_signal(lead.company_name)
        return HiringSignalBrief(
            company_name=lead.company_name,
            crunchbase_ref=f"cb_{slug.replace('-', '_')}",
            segment_recommendation=ICPSegment.RECENTLY_FUNDED,
            segment_confidence=ConfidenceLevel.MEDIUM,
            funding_signal=ScoredSignal(
                name="recent_funding",
                value="a recent growth signal consistent with Series A/B momentum",
                confidence=ConfidenceLevel.MEDIUM,
                evidence=["Public funding retrieval is not wired yet; this is a scaffolded placeholder."],
                source_refs=[source_refs[0]],
                freshness_days=45,
            ),
            job_post_signal=ScoredSignal(
                name="job_post_velocity",
                value="public engineering hiring activity appears present but not yet quantified",
                confidence=ConfidenceLevel.LOW,
                evidence=["Job-post scraping scaffold exists; velocity calculation is still pending."],
                source_refs=[source_refs[1]],
            ),
            layoff_signal=layoff_signal,
            leadership_change_signal=ScoredSignal(
                name="leadership_change",
                value="leadership-change detection is pending press-release retrieval",
                confidence=ConfidenceLevel.LOW,
                evidence=["Leadership-change enrichment is a placeholder in this scaffold."],
            ),
            ai_maturity_score=1,
            ai_maturity_reasoning=[
                "The current scaffold assumes light but non-zero AI readiness.",
                "Replace this with weighted public-signal scoring before evaluation.",
            ],
            bench_match_summary="Bench match is currently inferred as moderate for Python and data work until bench inputs are wired.",
            source_refs=source_refs + layoff_signal.source_refs,
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
